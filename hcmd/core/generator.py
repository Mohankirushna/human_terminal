from typing import List
from ..constants import CommandType, OS
from .detector import get_os, get_system_directory

class CommandGenerator:

    def __init__(self, os_type: OS = None):
        self.os = os_type or get_os()

    def generate(self, intent: CommandType, args: List[str]) -> str:

        if intent == CommandType.NAVIGATION:
            text = args[0].lower()
            for key in ["downloads", "desktop", "documents", "home"]:
                if key in text:
                    return f"cd {get_system_directory(key, self.os)}"
            return f"cd {args[0]}"

        if intent == CommandType.LIST_FILES:
            if self.os == OS.WINDOWS:
                return "Get-ChildItem"
            return "ls -la"


        if intent == CommandType.CREATE:
            name = args[0]
            return f"type nul > {name}" if self.os == OS.WINDOWS else f"touch {name}"

        if intent == CommandType.DELETE:
            name = args[0]
            return f"del {name}" if self.os == OS.WINDOWS else f"rm {name}"

        if intent == CommandType.COPY:
            src, dst = args
            return f"copy {src} {dst}" if self.os == OS.WINDOWS else f"cp {src} {dst}"

        if intent == CommandType.MOVE:
            src, dst = args
            return f"move {src} {dst}" if self.os == OS.WINDOWS else f"mv {src} {dst}"

        return ""
