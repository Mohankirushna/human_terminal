import sys
import os

from hcmd.core.executor import CommandExecutor
from hcmd.core.context_resolver import resolve_context
from hcmd.core.nlp import interpret
from hcmd.constants import OS
from hcmd.core.context import SystemContext
from hcmd.core.safety import validate_command

def normalize_path(path: str, ctx: SystemContext) -> str | None:
    if not path:
        return None

    if ctx.os_type == OS.WINDOWS:
        known = {
            "downloads": os.path.join(os.environ["USERPROFILE"], "Downloads"),
            "documents": os.path.join(os.environ["USERPROFILE"], "Documents"),
            "desktop": os.path.join(os.environ["USERPROFILE"], "Desktop"),
        }
        p = known.get(path.lower(), path)
        if not os.path.isabs(p):
            p = os.path.abspath(p)
        return p

    known = {
        "downloads": os.path.expanduser("~/Downloads"),
        "documents": os.path.expanduser("~/Documents"),
        "desktop": os.path.expanduser("~/Desktop"),
    }
    return known.get(path.lower(), path)


def build_command(intent: str, data: dict, ctx: SystemContext) -> str | None:
    os_type = ctx.os_type

    if intent == "LIST_FILES":
        return "Get-ChildItem" if os_type == OS.WINDOWS else "ls -la"

    if intent == "PWD":
        return "Get-Location" if os_type == OS.WINDOWS else "pwd"

    if intent == "NAVIGATION":
        raw = data.get("path")
        path = normalize_path(raw, ctx)
        if not path:
            return None
        if not os.path.isabs(path):
            path = os.path.join(ctx.cwd, path)
        return f'cd "{path}"'

    if intent == "MOVE_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        if os_type == OS.WINDOWS:
            return f'cmd /c move "{src}" "{dst}"'
        return f'mv "{src}" "{dst}"'

    if intent == "COPY_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        if os_type == OS.WINDOWS:
            return f'cmd /c copy "{src}" "{dst}"'
        return f'cp "{src}" "{dst}"'

    if intent == "CREATE_FILE":
        name = data.get("path")
        if not name:
            return None
        if os_type == OS.WINDOWS:
            return f'New-Item -ItemType File "{name}"'
        return f'touch "{name}"'

    if intent == "CREATE_DIR":
        name = data.get("path")
        if not name:
            return None
        if os_type == OS.WINDOWS:
            return f'New-Item -ItemType Directory "{name}"'
        return f'mkdir "{name}"'

    if intent == "DELETE_FILE":
        target = normalize_path(data.get("path"), ctx)
        if not target:
            return None
        if os_type == OS.WINDOWS:
            return f'del "{target}"'
        return f'rm "{target}"'

    if intent == "GIT_STATUS":
        return "git status" if ctx.is_git_repo else None

    if intent == "GIT_BRANCH":
        return "git branch --show-current" if ctx.is_git_repo else None
    if intent == "RENAME_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)

        if not src or not dst:
            return None

        if ctx.os_type == OS.WINDOWS:
            return f'Rename-Item "{src}" "{dst}"'
        return f'mv "{src}" "{dst}"'

    return None


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: hcmd <natural language command>")
        return 1

    text = " ".join(sys.argv[1:])

    result = interpret(text)
    if not result.get("ok"):
        print(f"ERROR: {result.get('reason')}")
        return 1

    ctx = resolve_context()
    intent = result["intent"]

    cmd = build_command(intent, result, ctx)
    if not cmd:
        print("ERROR: Unsupported or invalid command in current context")
        return 1

    safety = validate_command(intent, cmd, ctx)
    if not safety.safe:
        print(f"WARNING: {safety.warning}")
        ans = input("Proceed? [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborted by user")
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
