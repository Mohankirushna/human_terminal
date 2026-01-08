import warnings

warnings.filterwarnings(
    "ignore",
    message=".*weights_only=False.*",
    category=FutureWarning
)

import torch
import subprocess
import re
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
    TARGET_SPAN_MODEL_PATH,
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
).to(DEVICE).eval()

span_tokenizer = AutoTokenizer.from_pretrained(NAVIGATION_SPAN_MODEL_PATH)

nav_model = AutoModelForQuestionAnswering.from_pretrained(
    NAVIGATION_SPAN_MODEL_PATH
).to(DEVICE).eval()

src_model = AutoModelForQuestionAnswering.from_pretrained(
    SRC_SPAN_MODEL_PATH
).to(DEVICE).eval()

dst_model = AutoModelForQuestionAnswering.from_pretrained(
    DST_SPAN_MODEL_PATH
).to(DEVICE).eval()

object_model = AutoModelForQuestionAnswering.from_pretrained(
    OBJECT_SPAN_MODEL_PATH
).to(DEVICE).eval()

target_model = AutoModelForQuestionAnswering.from_pretrained(
    TARGET_SPAN_MODEL_PATH
).to(DEVICE).eval()

rename_model = DualSpanQA("distilbert-base-uncased").to(DEVICE)
rename_model.load_state_dict(
    torch.load(f"{RENAME_SPAN_MODEL_PATH}/pytorch_model.bin", map_location=DEVICE)
)
rename_model.eval()

git_add_model = AutoModelForQuestionAnswering.from_pretrained(
    GIT_ADD_MODEL_PATH
).to(DEVICE).eval()

git_checkout_model = AutoModelForQuestionAnswering.from_pretrained(
    GIT_CHECKOUT_MODEL_PATH
).to(DEVICE).eval()

git_clone_model = AutoModelForQuestionAnswering.from_pretrained(
    GIT_CLONE_MODEL_PATH
).to(DEVICE).eval()

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def in_git_repo():
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


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

    s = torch.argmax(start_probs).item()
    e = torch.argmax(end_probs).item()

    if e < s:
        return None, 0.0

    span = text[offsets[s][0]:offsets[e][1]].strip()
    conf = (start_probs[s] * end_probs[e]).item()
    return span, conf


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

    def decode(start, end):
        s = torch.argmax(start).item()
        e = torch.argmax(end).item()
        if e < s:
            return None, 0.0
        span = text[offsets[s][0]:offsets[e][1]].strip()
        conf = (torch.softmax(start, -1)[0][s] *
                torch.softmax(end, -1)[0][e]).item()
        return span, conf

    src, src_conf = decode(out["src_start_logits"], out["src_end_logits"])
    dst, dst_conf = decode(out["dst_start_logits"], out["dst_end_logits"])
    return src, src_conf, dst, dst_conf


# --------------------------------------------------
# MAIN INTERPRETER
# --------------------------------------------------

def interpret(text: str) -> dict:
    t = text.lower().strip()

    # ---------- HARD PRONOUN DELETE (Phase 8) ----------
    if t in ("delete it", "remove it", "erase it"):
        if memory.last_path:
            intent = "DELETE_FILE"
            intent_conf = 1.0
            result = {
                "ok": True,
                "intent": intent,
                "confidence": intent_conf,
                "path": memory.last_path,
                "from_pronoun": True   # 🔑 ADD THIS
            }
            return result
        else:
            return {"ok": False, "reason": "Nothing to delete"}

    else:
        intent = None
        intent_conf = 0.0

        # ---------- RULE INTENT ----------
        rule = rule_intent(text)
        if rule:
            intent = rule
            intent_conf = 1.0

        # ---------- GIT FOLLOW-UPS (Phase 8) ----------
        elif in_git_repo() and memory.last_git_intent and "git" not in t:
            if re.search(r"\bbranch\b", t):
                intent = "GIT_BRANCH"
                intent_conf = 1.0
            elif re.search(r"\bcheckout\b", t):
                intent = "GIT_CHECKOUT"
                intent_conf = 1.0
            elif re.search(r"\badd\b", t):
                intent = "GIT_ADD"
                intent_conf = 1.0
            elif re.search(r"\bcommit\b", t):
                intent = "GIT_COMMIT"
                intent_conf = 1.0

        # ---------- ML FALLBACK ----------
        if intent is None:
            inputs = intent_tokenizer(text, return_tensors="pt").to(DEVICE)
            with torch.no_grad():
                logits = intent_model(**inputs).logits

            probs = torch.softmax(logits, dim=-1)[0]
            idx = torch.argmax(probs).item()
            intent_conf = probs[idx].item()
            intent = intent_model.config.id2label[idx]

            if intent_conf < INTENT_CONF_THRESHOLD:
                return {"ok": False, "reason": "Low intent confidence"}

    result = {
        "ok": True,
        "intent": intent,
        "confidence": intent_conf
    }

    print("DEBUG INTENT:", intent)

    # ---------- PATTERNS ----------
    if intent in ("DELETE_FILE", "MOVE_FILE", "COPY_FILE"):
        pattern = detect_pattern(text)
        if isinstance(pattern, str) and any(c in pattern for c in "*?"):
            result["pattern"] = pattern

    # ---------- SPANS ----------
    if intent == "NAVIGATION":
        path, conf = _extract_span(text, nav_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path

    elif intent in ("MOVE_FILE", "COPY_FILE"):
        result["src"], _ = _extract_span(text, src_model)
        result["dst"], _ = _extract_span(text, dst_model)

    elif intent == "RENAME_FILE":
        src, sc, dst, dc = _extract_rename_spans(text, rename_model)
        if sc >= SPAN_CONF_THRESHOLD:
            result["src"] = src
        if dc >= SPAN_CONF_THRESHOLD:
            result["dst"] = dst
        if src and dst and src == dst:
            return {"ok": False, "reason": "Rename source and destination identical"}

    elif intent in ("CREATE_FILE", "DELETE_FILE"):
        obj, conf = _extract_span(text, object_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = obj

    elif intent == "CREATE_DIR" or intent == "DELETE_DIR":
        path, conf = _extract_span(text, nav_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path

    elif intent == "GIT_ADD":
        path, conf = _extract_span(text, git_add_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["path"] = path

    elif intent == "GIT_CHECKOUT":
        branch, conf = _extract_span(text, git_checkout_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["branch"] = branch

    elif intent == "GIT_CLONE":
        repo, conf = _extract_span(text, git_clone_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["repo"] = repo

    elif intent == "PROCESS_KILL":
        target, conf = _extract_span(text, target_model)
        if conf >= SPAN_CONF_THRESHOLD:
            result["target"] = target

    # ---------- MEMORY FALLBACK ----------
    if intent in ("DELETE_FILE", "DELETE_DIR") and not result.get("path"):
        result["path"] = memory.last_path

    if intent in ("MOVE_FILE", "COPY_FILE", "RENAME_FILE"):
        result.setdefault("src", memory.last_src)
        result.setdefault("dst", memory.last_dst)

    return result
