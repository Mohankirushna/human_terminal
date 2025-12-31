from typing import List, Tuple
from ..constants import CommandType

def validate(intent: CommandType, args: List[str]) -> Tuple[bool, str]:

    if intent == CommandType.DELETE:
        if not args or "*" in args[0] or ".." in args[0]:
            return False, "Unsafe delete target"

    if intent in (CommandType.COPY, CommandType.MOVE):
        if len(args) != 2:
            return False, "Source and destination required"

    return True, ""
