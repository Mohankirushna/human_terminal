import sys
from hcmd.core.executor import CommandExecutor
from hcmd.core.nlp import interpret
from hcmd.core.detector import get_os
from hcmd.constants import OS

import os

def normalize_path(path, os_type):
    if os_type == OS.WINDOWS:
        known = {
            "downloads": os.path.join(os.environ["USERPROFILE"], "Downloads"),
            "documents": os.path.join(os.environ["USERPROFILE"], "Documents"),
            "desktop": os.path.join(os.environ["USERPROFILE"], "Desktop"),
        }

        p = known.get(path.lower(), path)

        if not os.path.isabs(p):
            p = os.path.abspath(p)

        return p

    if path.lower() == "downloads":
        return os.path.expanduser("~/Downloads")
    if path.lower() == "documents":
        return os.path.expanduser("~/Documents")
    if path.lower() == "desktop":
        return os.path.expanduser("~/Desktop")

    return path


def build_command(intent, data, os_type):
    print("DEBUG: Building command for intent =", intent)
    if intent == "LIST_FILES":
        if os_type == OS.WINDOWS:
            return "Get-ChildItem"
        return "ls -la"

    if intent == "PWD":
        if os_type == OS.WINDOWS:
            return "Get-Location"
        return "pwd"

    if intent == "NAVIGATION":
        path = data["path"]
        return f"cd {path}"

    if intent == "MOVE_FILE":
        src = normalize_path(data["src"], os_type)
        dst = normalize_path(data["dst"], os_type)
        print("DEBUG:")
        print("  intent = MOVE_FILE")
        print("  raw src =", data["src"])
        print("  raw dst =", data["dst"])
        print("  resolved src =", src)
        print("  resolved dst =", dst)
        if os_type == OS.WINDOWS:
            return f'cmd /c move "{src}" "{dst}"'
        return f'mv "{src}" "{dst}"'


    if intent == "COPY_FILE":
        src = normalize_path(data["src"], os_type)
        dst = normalize_path(data["dst"], os_type)
        if os_type == OS.WINDOWS:
            return f'cmd /c copy "{src}" "{dst}"'
        return f'cp "{src}" "{dst}"'


    if intent == "CREATE_FILE":
        name = data.get("name")
        if not name:
            return None
        if os_type == OS.WINDOWS:
            return f"New-Item -ItemType File {name}"
        return f"touch {name}"

    if intent == "CREATE_DIR":
        name = data.get("name")
        if not name:
            return None
        if os_type == OS.WINDOWS:
            return f"New-Item -ItemType Directory {name}"
        return f"mkdir {name}"

    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: hcmd <natural language command>")
        return 1

    text = " ".join(sys.argv[1:])

    result = interpret(text)
    if not result.get("ok"):
        print(f"ERROR: {result.get('reason')}")
        return 1

    os_type = get_os()
    intent = result["intent"]

    cmd = build_command(intent, result, os_type)
    if not cmd:
        print("ERROR: Unsupported intent")
        return 1

    executor = CommandExecutor()
    success, output = executor.execute(cmd)

    if not success:
        print(f"ERROR: {output}")
        return 1

    if output:
        print(output)

    return 0

def run():
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)

if __name__ == "__main__":
    run()
