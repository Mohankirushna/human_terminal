import sys
import os

from hcmd.core.executor import CommandExecutor
from hcmd.core.context_resolver import resolve_context
from hcmd.core.nlp import interpret
from hcmd.constants import OS
from hcmd.core.context import SystemContext
from hcmd.core.safety import validate_command
from hcmd.core.ambiguity import detect_ambiguity, ClarificationRequest
from hcmd.core.memory import memory
from hcmd.core.pattern_executor import resolve_pattern


# --------------------------------------------------
# Path normalization
# --------------------------------------------------
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


# --------------------------------------------------
# Command builder (SINGLE TARGET ONLY)
# --------------------------------------------------
def build_command(intent: str, data: dict, ctx: SystemContext) -> str | None:
    os_type = ctx.os_type

    if intent == "LIST_FILES":
        return "Get-ChildItem" if os_type == OS.WINDOWS else "ls -la"

    if intent == "PWD":
        return "Get-Location" if os_type == OS.WINDOWS else "pwd"

    if intent == "NAVIGATION":
        path = normalize_path(data.get("path"), ctx)
        if not path:
            return None
        return f'cd "{path}"'

    if intent == "MOVE_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        return (
            f'cmd /c move "{src}" "{dst}"'
            if os_type == OS.WINDOWS
            else f'mv "{src}" "{dst}"'
        )

    if intent == "COPY_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        return (
            f'cmd /c copy "{src}" "{dst}"'
            if os_type == OS.WINDOWS
            else f'cp "{src}" "{dst}"'
        )

    if intent == "CREATE_FILE":
        name = data.get("path")
        if not name:
            return None
        return (
            f'New-Item -ItemType File "{name}"'
            if os_type == OS.WINDOWS
            else f'touch "{name}"'
        )

    if intent == "CREATE_DIR":
        name = data.get("path")
        if not name:
            return None
        return (
            f'New-Item -ItemType Directory "{name}"'
            if os_type == OS.WINDOWS
            else f'mkdir "{name}"'
        )

    if intent == "DELETE_FILE":
        target = normalize_path(data.get("path"), ctx)
        if not target:
            return None
        return f'del "{target}"' if os_type == OS.WINDOWS else f'rm "{target}"'

    if intent == "RENAME_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        return (
            f'Rename-Item "{src}" "{dst}"'
            if os_type == OS.WINDOWS
            else f'mv "{src}" "{dst}"'
        )

    return None


# --------------------------------------------------
# MAIN
# --------------------------------------------------
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

    # ---------- Ambiguity ----------
    clarification = detect_ambiguity(intent, result, ctx)
    if isinstance(clarification, ClarificationRequest):
        print(f"CLARIFICATION REQUIRED: {clarification.reason}")
        for i, opt in enumerate(clarification.options, 1):
            print(f"{i}) {opt}")

        choice = input("Select option number: ").strip()
        if not choice.isdigit():
            return 1

        resolved = clarification.options[int(choice) - 1]
        if intent in ("DELETE_FILE", "READ_FILE"):
            result["path"] = resolved
        else:
            result["src"] = resolved

    # ---------- Pattern execution (Phase 7.3) ----------
    if "pattern" in result:
        files = resolve_pattern(result["pattern"], ctx)
        if not files:
            print("No files matched the pattern")
            return 0

        print(f"Matched {len(files)} files")
        if intent in ("DELETE_FILE", "MOVE_FILE", "COPY_FILE"):
            if input("Proceed? [y/N]: ").lower() != "y":
                return 1

        executor = CommandExecutor()
        for f in files:
            per_cmd = build_command(intent, {**result, "path": f, "src": f}, ctx)
            executor.execute(per_cmd)

        return 0

    # ---------- Normal execution ----------
    cmd = build_command(intent, result, ctx)
    if not cmd:
        print("ERROR: Unsupported or invalid command")
        return 1

    safety = validate_command(intent, cmd, ctx)
    if not safety.safe:
        if input(f"{safety.warning} Proceed? [y/N]: ").lower() != "y":
            return 1

    executor = CommandExecutor()
    executor.execute(cmd)

    memory.last_intent = intent
    memory.last_path = result.get("path") or memory.last_path
    memory.last_src = result.get("src") or memory.last_src
    memory.last_dst = result.get("dst") or memory.last_dst

    return 0


def run():
    sys.exit(main())


if __name__ == "__main__":
    run()
