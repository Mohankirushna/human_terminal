import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering
)

from ..constants import (
    INTENT_MODEL_PATH,
    NAVIGATION_SPAN_MODEL_PATH,
    SRC_SPAN_MODEL_PATH,
    DST_SPAN_MODEL_PATH,
    OBJECT_SPAN_MODEL_PATH,
    RENAME_SPAN_MODEL_PATH,
    INTENT_CONF_THRESHOLD,
    SPAN_CONF_THRESHOLD
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

rename_model = AutoModelForQuestionAnswering.from_pretrained(
    RENAME_SPAN_MODEL_PATH
).to(DEVICE)

for m in (nav_model, src_model, dst_model, object_model, rename_model):
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
        src, src_conf = _extract_span(text, rename_model)
        dst, dst_conf = _extract_span(text, rename_model)

        if src_conf >= SPAN_CONF_THRESHOLD:
            result["src"] = src
        if dst_conf >= SPAN_CONF_THRESHOLD:
            result["dst"] = dst

        if result.get("src") == result.get("dst"):
            return {"ok": False, "reason": "Rename source and destination identical"}

    # ---------- CREATE / DELETE ----------
    elif intent in ("DELETE_FILE", "CREATE_FILE", "CREATE_DIR"):
        obj, obj_conf = _extract_span(text, object_model)
        if obj_conf >= SPAN_CONF_THRESHOLD:
            result["path"] = obj

    # ---------- MEMORY FALLBACK ----------
    if intent in ("DELETE_FILE", "RENAME_FILE"):
        if not result.get("path") and memory.last_path:
            result["path"] = memory.last_path

    if intent in ("MOVE_FILE", "COPY_FILE", "RENAME_FILE"):
        if not result.get("src") and memory.last_src:
            result["src"] = memory.last_src
        if not result.get("dst") and memory.last_dst:
            result["dst"] = memory.last_dst

    return result
