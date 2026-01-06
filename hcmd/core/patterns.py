import os
import re
from typing import List
from hcmd.core.context import SystemContext


EXT_MAP = {
    "text": ".txt",
    "txt": ".txt",
    "csv": ".csv",
    "python": ".py",
    "py": ".py",
    "log": ".log",
    "json": ".json",
}


def detect_pattern(text: str) -> dict | None:
    text = text.lower()

    if "all files" in text or "everything" in text:
        return {"type": "ALL"}

    m = re.search(r"\.(\w+)", text)
    if m:
        return {"type": "EXT", "ext": f".{m.group(1)}"}

    for k, v in EXT_MAP.items():
        if k in text and "file" in text:
            return {"type": "EXT", "ext": v}

    return None


def resolve_pattern(pattern: dict, ctx: SystemContext) -> List[str]:
    files = []

    for name in os.listdir(ctx.cwd):
        path = os.path.join(ctx.cwd, name)
        if not os.path.isfile(path):
            continue

        if pattern["type"] == "ALL":
            files.append(path)

        elif pattern["type"] == "EXT" and name.endswith(pattern["ext"]):
            files.append(path)

    return files
