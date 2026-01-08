import warnings

warnings.filterwarnings(
    "ignore",
    message=".*weights_only=False.*",
    category=FutureWarning
)

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering
)
from hcmd.core.rename_model import DualSpanQA


from ..constants import (
    INTENT_MODEL_PATH,
    NAVIGATION_SPAN_MODEL_PATH,
    SRC_SPAN_MODEL_PATH,
    DST_SPAN_MODEL_PATH,
    OBJECT_SPAN_MODEL_PATH,
    RENAME_SPAN_MODEL_PATH,
    INTENT_CONF_THRESHOLD,
    SPAN_CONF_THRESHOLD,
    GIT_ADD_MODEL_PATH,
    GIT_CHECKOUT_MODEL_PATH,
    GIT_CLONE_MODEL_PATH
)

from hcmd.core.intent_rules import rule_intent
from hcmd.core.memory import memory
from hcmd.core.patterns import detect_pattern

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --------------------------------------------------
# Load models
# --------------------------------------------------

intent_tokenizer = AutoTokenizer.from_pretrained(INTENT_MODEL_PATH)
intent_model = AutoModelForSequenceClassification.from_pretrained(
    INTENT_MODEL_PATH
).to(DEVICE)
intent_model.eval()

span_tokenizer = AutoTokenizer.from_pretrained(NAVIGATION_SPAN_MODEL_PATH)

nav_model = AutoModelForQuestionAnswering.from_pretrained(
    NAVIGATION_SPAN_MODEL_PATH
).to(DEVICE)

src_model = AutoModelForQuestionAnswering.from_pretrained(
    SRC_SPAN_MODEL_PATH
).to(DEVICE)

dst_model = AutoModelForQuestionAnswering.from_pretrained(
    DST_SPAN_MODEL_PATH
).to(DEVICE)

object_model = AutoModelForQuestionAnswering.from_pretrained(
    OBJECT_SPAN_MODEL_PATH
).to(DEVICE)

rename_model = DualSpanQA("distilbert-base-uncased").to(DEVICE)
rename_model.load_state_dict(
    torch.load(f"{RENAME_SPAN_MODEL_PATH}/pytorch_model.bin", map_location=DEVICE)
)
rename_model.eval()


git_add_model = AutoModelForQuestionAnswering.from_pretrained(
    GIT_ADD_MODEL_PATH
).to(DEVICE)

git_checkout_model = AutoModelForQuestionAnswering.from_pretrained(
    GIT_CHECKOUT_MODEL_PATH
).to(DEVICE)

git_clone_model = AutoModelForQuestionAnswering.from_pretrained(
    GIT_CLONE_MODEL_PATH
).to(DEVICE)

for m in (git_add_model, git_checkout_model, git_clone_model):
    m.eval()

for m in (nav_model, src_model, dst_model, object_model):
    m.eval()


# --------------------------------------------------
# Span extraction helper
# --------------------------------------------------

def _extract_span(text: str, model):
    inputs = span_tokenizer(
        text,
        return_tensors="pt",
        return_offsets_mapping=True,
        truncation=True
    )

    offsets = inputs.pop("offset_mapping")[0]
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        out = model(**inputs)

    start_probs = torch.softmax(out.start_logits, dim=-1)[0]
    end_probs = torch.softmax(out.end_logits, dim=-1)[0]

    start_idx = torch.argmax(start_probs).item()
    end_idx = torch.argmax(end_probs).item()

    if end_idx < start_idx:
        return None, 0.0

    start_char = offsets[start_idx][0]
    end_char = offsets[end_idx][1]

    span_text = text[start_char:end_char].strip()
    confidence = (start_probs[start_idx] * end_probs[end_idx]).item()

    return span_text, confidence

def _extract_rename_spans(text: str, model):
    enc = span_tokenizer(
        text,
        return_tensors="pt",
        return_offsets_mapping=True,
        truncation=True
    )

    offsets = enc.pop("offset_mapping")[0]
    enc = {k: v.to(DEVICE) for k, v in enc.items()}

    with torch.no_grad():
        out = model(**enc)

    def decode(start_logits, end_logits):
        start_probs = torch.softmax(start_logits, dim=-1)[0]
        end_probs   = torch.softmax(end_logits, dim=-1)[0]

        s = torch.argmax(start_probs).item()
        e = torch.argmax(end_probs).item()

        if e < s:
            return None, 0.0

        text_span = text[offsets[s][0]:offsets[e][1]].strip()
        conf = (start_probs[s] * end_probs[e]).item()
        return text_span, conf

    src, src_conf = decode(out["src_start_logits"], out["src_end_logits"])
    dst, dst_conf = decode(out["dst_start_logits"], out["dst_end_logits"])

    return src, src_conf, dst, dst_conf

# --------------------------------------------------
# MAIN INTERPRETER
# --------------------------------------------------

def interpret(text: str) -> dict:
    """
    Deterministic hybrid NLP interpreter:
    - Rule intent OR ML intent
    - ALWAYS run span extraction
    - Pattern detection does NOT short-circuit spans
    """
    
    # ---------- INTENT ----------
    rule = rule_intent(text)

    if rule:
        intent = rule
        intent_conf = 1.0
    else:
        inputs = intent_tokenizer(text, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            logits = intent_model(**inputs).logits

        probs = torch.softmax(logits, dim=-1)[0]
        intent_id = torch.argmax(probs).item()
        intent_conf = probs[intent_id].item()
        intent = intent_model.config.id2label[intent_id]

        if intent_conf < INTENT_CONF_THRESHOLD:
            return {"ok": False, "reason": "Low intent confidence"}

    result = {
        "ok": True,
        "intent": intent,
        "confidence": intent_conf
    }
    print("DEBUG INTENT:", intent)

    # ---------- PATTERN DETECTION (non-blocking) ----------
    if intent in ("DELETE_FILE", "MOVE_FILE", "COPY_FILE"):
        pattern = detect_pattern(text)

        if pattern:
            # If detect_pattern returns a dict, extract the actual pattern
            if isinstance(pattern, dict):
                pattern = pattern.get("pattern")

            # ONLY treat as pattern if wildcard characters exist
            if isinstance(pattern, str) and any(ch in pattern for ch in ("*", "?")):
                result["pattern"] = pattern


    # ---------- NAVIGATION ----------
    if intent == "NAVIGATION":
        path, conf = _extract_span(text, nav_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path
        else:
            return {"ok": False, "reason": "Low navigation span confidence"}

    # ---------- MOVE / COPY ----------
    elif intent in ("MOVE_FILE", "COPY_FILE"):
        src, src_conf = _extract_span(text, src_model)
        dst, dst_conf = _extract_span(text, dst_model)

        if src_conf >= SPAN_CONF_THRESHOLD:
            result["src"] = src
        if dst_conf >= SPAN_CONF_THRESHOLD:
            result["dst"] = dst

    # ---------- RENAME ----------
    elif intent == "RENAME_FILE":
        src, src_conf, dst, dst_conf = _extract_rename_spans(text, rename_model)

        if src_conf >= SPAN_CONF_THRESHOLD:
            result["src"] = src
        if dst_conf >= SPAN_CONF_THRESHOLD:
            result["dst"] = dst

        # This check is now a true safety guard, not a hack
        if result.get("src") and result.get("dst"):
            if result["src"] == result["dst"]:
                return {"ok": False, "reason": "Rename source and destination identical"}


    # ---------- CREATE / DELETE ----------
    elif intent in ("CREATE_DIR",):
        path, conf = _extract_span(text, nav_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path
        else:
            return {"ok": False, "reason": "Low directory span confidence"}

    elif intent in ("DELETE_DIR",):
        path, conf = _extract_span(text, nav_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path
        else:
            return {"ok": False, "reason": "Low directory span confidence"}

    elif intent in ("DELETE_FILE", "CREATE_FILE"):
        obj, obj_conf = _extract_span(text, object_model)
        if obj_conf >= SPAN_CONF_THRESHOLD:
            result["path"] = obj
    elif intent == "GIT_ADD":
        path, conf = _extract_span(text, git_add_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path
        else :
            return {"ok": False, "reason": "Low git add span confidence"}
    elif intent == "GIT_CHECKOUT":
        branch, conf = _extract_span(text, git_checkout_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["branch"] = branch
        else :
            return {"ok": False, "reason": "Low git checkout span confidence"}
    elif intent == "GIT_CLONE":
        repo, conf = _extract_span(text, git_clone_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["repo"] = repo
        else :
            return {"ok": False, "reason": "Low git clone span confidence"}

    # ---------- MEMORY FALLBACK ----------
    if intent in ("DELETE_FILE", "DELETE_DIR"):
        if not result.get("path") and memory.last_path:
            result["path"] = memory.last_path


    if intent in ("MOVE_FILE", "COPY_FILE", "RENAME_FILE"):
        if not result.get("src") and memory.last_src:
            result["src"] = memory.last_src
        if not result.get("dst") and memory.last_dst:
            result["dst"] = memory.last_dst

    return result
