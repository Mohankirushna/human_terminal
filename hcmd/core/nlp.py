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
    INTENT_CONF_THRESHOLD,
    SPAN_CONF_THRESHOLD
)

from hcmd.core.intent_rules import rule_intent


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ----------------------------
# Load INTENT model
# ----------------------------
intent_tokenizer = AutoTokenizer.from_pretrained(INTENT_MODEL_PATH)
intent_model = AutoModelForSequenceClassification.from_pretrained(
    INTENT_MODEL_PATH
).to(DEVICE)
intent_model.eval()

# ----------------------------
# Load SPAN tokenizer
# ----------------------------
span_tokenizer = AutoTokenizer.from_pretrained(NAVIGATION_SPAN_MODEL_PATH)

# ----------------------------
# Load SPAN models
# ----------------------------
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

nav_model.eval()
src_model.eval()
dst_model.eval()
object_model.eval()


# ----------------------------
# Span extraction helper
# ----------------------------
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
        return "", 0.0

    start_char = offsets[start_idx][0]
    end_char = offsets[end_idx][1]

    span_text = text[start_char:end_char].strip()
    confidence = (start_probs[start_idx] * end_probs[end_idx]).item()

    return span_text, confidence


# ----------------------------
# MAIN INTERPRETER
# ----------------------------
def interpret(text: str) -> dict:
    # ---- Rule-based intent short-circuit (intent ONLY)
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

    # ---- NAVIGATION
    if intent == "NAVIGATION":
        span, conf = _extract_span(text, nav_model)
        if conf < SPAN_CONF_THRESHOLD:
            return {"ok": False, "reason": "Low navigation span confidence"}
        result["path"] = span

    # ---- MOVE / COPY
    if intent in ("MOVE_FILE", "COPY_FILE"):
        src, src_conf = _extract_span(text, src_model)
        dst, dst_conf = _extract_span(text, dst_model)

        if src_conf < SPAN_CONF_THRESHOLD or dst_conf < SPAN_CONF_THRESHOLD:
            return {"ok": False, "reason": "Low src/dst confidence"}

        result["src"] = src
        result["dst"] = dst

    # ---- CREATE / DELETE / MKDIR
    if intent in ("DELETE_FILE", "CREATE_FILE", "CREATE_DIR"):
        obj, obj_conf = _extract_span(text, object_model)

        if obj_conf < SPAN_CONF_THRESHOLD:
            return {"ok": False, "reason": "Low object span confidence"}

        result["path"] = obj

    return result
