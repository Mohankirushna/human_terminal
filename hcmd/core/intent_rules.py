import re
from typing import Optional

RULE_INTENTS = {
    "LIST_FILES": [
        r"^\s*ls\s*$",
        r"^\s*list\s*$",
        r"^\s*list files\s*$",
        r"^\s*show files\s*$",
    ]
}
def rule_intent(text: str) -> Optional[str]:
    t = text.lower().strip()

    for intent, patterns in RULE_INTENTS.items():
        for pat in patterns:
            if re.match(pat, t):
                return intent

    return None
