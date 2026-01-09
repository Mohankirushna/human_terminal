import re

CONNECTORS = r"\b(and then|then|and|;)\b"

def split_into_steps(text: str) -> list[str]:
    parts = re.split(CONNECTORS, text, flags=re.IGNORECASE)
    steps = []

    for p in parts:
        p = p.strip()
        if not p or p.lower() in ("and", "then", "and then", ";"):
            continue
        steps.append(p)

    return steps
