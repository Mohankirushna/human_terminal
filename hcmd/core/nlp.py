import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForQuestionAnswering
from ..constants import (
    INTENT_MODEL_PATH,
    NAVIGATION_SPAN_MODEL_PATH,
    SRC_SPAN_MODEL_PATH,
    DST_SPAN_MODEL_PATH,
    INTENT_CONF_THRESHOLD,
    SPAN_CONF_THRESHOLD
)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

intent_tokenizer = AutoTokenizer.from_pretrained(INTENT_MODEL_PATH)
intent_model = AutoModelForSequenceClassification.from_pretrained(INTENT_MODEL_PATH).to(DEVICE)
intent_model.eval()

span_tokenizer = AutoTokenizer.from_pretrained(NAVIGATION_SPAN_MODEL_PATH)

nav_model = AutoModelForQuestionAnswering.from_pretrained(NAVIGATION_SPAN_MODEL_PATH).to(DEVICE)
src_model = AutoModelForQuestionAnswering.from_pretrained(SRC_SPAN_MODEL_PATH).to(DEVICE)
dst_model = AutoModelForQuestionAnswering.from_pretrained(DST_SPAN_MODEL_PATH).to(DEVICE)

nav_model.eval()
src_model.eval()
dst_model.eval()

def _extract_span(text, model):
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

    span_text = text[start_char:end_char]

    confidence = (start_probs[start_idx] * end_probs[end_idx]).item()

    return span_text.strip(), confidence

def interpret(text):
    inputs = intent_tokenizer(text, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        logits = intent_model(**inputs).logits

    probs = torch.softmax(logits, dim=-1)[0]
    intent_id = torch.argmax(probs).item()
    intent_conf = probs[intent_id].item()
    intent = intent_model.config.id2label[intent_id]

    if intent_conf < INTENT_CONF_THRESHOLD:
        return {"ok": False, "reason": "Low intent confidence"}

    result = {"intent": intent, "confidence": intent_conf}

    if intent == "NAVIGATION":
        span, conf = _extract_span(text, nav_model)
        if conf < SPAN_CONF_THRESHOLD:
            return {"ok": False, "reason": "Low navigation span confidence"}
        result["path"] = span

    if intent in ("MOVE_FILE", "COPY_FILE"):
        src, src_conf = _extract_span(text, src_model)
        dst, dst_conf = _extract_span(text, dst_model)

        if src_conf < SPAN_CONF_THRESHOLD or dst_conf < SPAN_CONF_THRESHOLD:
            return {"ok": False, "reason": "Low src/dst confidence"}

        result["src"] = src
        result["dst"] = dst

    result["ok"] = True
    return result
