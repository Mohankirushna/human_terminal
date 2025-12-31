from typing import Tuple, List
from ..constants import CommandType

class RuleParser:

    def parse(self, text: str) -> Tuple[CommandType, List[str]]:
        t = text.lower().strip()

        if any(x in t for x in ["go to", "cd", "navigate"]):
            return CommandType.NAVIGATION, [text]

        if any(x in t for x in ["list files", "show files", "list directory", "show contents"]):
            return CommandType.LIST_FILES, []

        if any(x in t for x in ["create file", "make file", "new file", "touch"]):
            return CommandType.CREATE, [t.split()[-1]]

        if any(x in t for x in ["delete", "remove"]):
            return CommandType.DELETE, [t.split()[-1]]

        if "copy" in t and "to" in t:
            a, b = t.split("to")
            return CommandType.COPY, [a.split()[-1], b.strip()]

        if "move" in t and "to" in t:
            a, b = t.split("to")
            return CommandType.MOVE, [a.split()[-1], b.strip()]

        return CommandType.UNKNOWN, []
