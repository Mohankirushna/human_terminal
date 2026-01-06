from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionMemory:
    last_intent: Optional[str] = None
    last_path: Optional[str] = None
    last_src: Optional[str] = None
    last_dst: Optional[str] = None


# singleton (CLI lifetime)
memory = SessionMemory()
