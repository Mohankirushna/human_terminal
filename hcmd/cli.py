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
def normalize_path(path: str | None, ctx: SystemContext) -> str | None:
    if not path:
        return None

    if ctx.os_type == OS.WINDOWS:
        known = {
            "downloads": os.path.join(os.environ["USERPROFILE"], "Downloads"),
            "documents": os.path.join(os.environ["USERPROFILE"], "Documents"),
            "desktop": os.path.join(os.environ["USERPROFILE"], "Desktop"),
        }
        p = known.get(path.lower(), path)
        return os.path.abspath(p)

    known = {
        "downloads": os.path.expanduser("~/Downloads"),
        "documents": os.path.expanduser("~/Documents"),
        "desktop": os.path.expanduser("~/Desktop"),
    }
    return known.get(path.lower(), path)


# --------------------------------------------------
# Command builder (single-target only)
# --------------------------------------------------
def build_command(intent: str, data: dict, ctx: SystemContext) -> str | None:
    os_type = ctx.os_type

    if intent == "LIST_FILES":
        return "Get-ChildItem" if os_type == OS.WINDOWS else "ls -la"

    if intent == "PWD":
        return "Get-Location" if os_type == OS.WINDOWS else "pwd"

    if intent == "NAVIGATION":
        path = normalize_path(data.get("path"), ctx)
        return f'cd "{path}"' if path else None

    if intent == "MOVE_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        print(src, dst)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        return (
            f'Move-Item "{src}" "{dst}"'
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
            f'Copy-Item "{src}" "{dst}"'
            if os_type == OS.WINDOWS
            else f'cp "{src}" "{dst}"'
        )

    if intent == "CREATE_FILE":
        name = data.get("path")
        return (
            f'New-Item -ItemType File "{name}"'
            if name and os_type == OS.WINDOWS
            else f'touch "{name}"' if name else None
        )

    if intent == "CREATE_DIR":
        name = data.get("path")
        return (
            f'New-Item -ItemType Directory "{name}"'
            if name and os_type == OS.WINDOWS
            else f'mkdir "{name}"' if name else None
        )

    if intent == "DELETE_FILE":
        target = normalize_path(data.get("path"), ctx)
        return (
            f'del "{target}"'
            if target and os_type == OS.WINDOWS
            else f'rm "{target}"' if target else None
        )

    if intent == "DELETE_DIR":
        target = normalize_path(data.get("path"), ctx)
        return (
            f'Remove-Item -Recurse -Force "{target}"'
            if target and os_type == OS.WINDOWS
            else f'rm -r "{target}"' if target else None
        )

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
        # ---------- SYSTEM ----------
    if intent == "SYSTEM_INFO":
        return (
            "systeminfo"
            if os_type == OS.WINDOWS
            else "uname -a"
        )

    if intent == "PROCESS_LIST":
        return (
            "tasklist"
            if os_type == OS.WINDOWS
            else "ps aux"
        )

    if intent == "NETWORK_INFO":
        return (
            "ipconfig"
            if os_type == OS.WINDOWS
            else "ifconfig"
        )
    if intent == "PROCESS_KILL":
        target = data.get("target")
        if not target:
            return None

        if ctx.os_type == OS.WINDOWS:
            if target.isdigit():
                return f'taskkill /PID {target} /F'
            else:
                return f'taskkill /IM {target}.exe /F'

        # Linux / macOS
        if target.isdigit():
            return f'kill {target}'
        else:
            return f'killall {target}'

    # ---------- GIT (no span required) ----------
    if intent == "GIT_STATUS":
        return "git status"

    if intent == "GIT_BRANCH":
        return "git branch"

    if intent == "GIT_LOG":
        return "git log --oneline --decorate --graph"

    if intent == "GIT_PULL":
        return "git pull"

    if intent == "GIT_PUSH":
        return "git push"
    
    if intent == "GIT_RESET":
        return "git reset"

    if intent == "GIT_STASH":
        return "git stash"
    if intent == "GIT_CLONE":
        repo = data.get("repo")
        if not repo:
            return None
        return f'git clone "{repo}"'

    if intent == "GIT_ADD":
        path = data.get("path")
        if not path:
            return None
        return f'git add "{path}"'

    if intent == "GIT_CHECKOUT":
        branch = data.get("branch")
        if not branch:
            return None
        return f'git checkout "{branch}"'
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
    if intent in ("DELETE_FILE", "DELETE_DIR") and not result.get("path"):
        if memory.last_path:
            result["path"] = memory.last_path
    # -------- Ambiguity (Phase 7.1) --------
    clarification = None

    if not (intent in ("DELETE_FILE", "DELETE_DIR") and result.get("path") == memory.last_path):
        if not result.get("from_pronoun"):
            clarification = detect_ambiguity(intent, result, ctx)



    if isinstance(clarification, ClarificationRequest):
        # Case 1: no options → missing information
        if not clarification.options:
            print(f"ERROR: {clarification.reason}")
            print("Please rephrase the command with more detail.")
            return 1

        # Case 2: real ambiguity → show menu
        print(f"CLARIFICATION REQUIRED: {clarification.reason}")
        for i, opt in enumerate(clarification.options, 1):
            print(f"{i}) {opt}")

        choice = input("Select option number: ").strip()
        if not choice.isdigit():
            print("Invalid selection")
            return 1

        idx = int(choice) - 1
        if idx < 0 or idx >= len(clarification.options):
            print("Invalid selection")
            return 1

        resolved = clarification.options[idx]

        if intent in ("DELETE_FILE", "READ_FILE"):
            result["path"] = resolved
        else:
            result["src"] = resolved

    # -------- Pattern execution (Phase 7.3) --------
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
            per_cmd = build_command(
                intent,
                {**result, "path": f, "src": f},
                ctx
            )

            if not per_cmd:
                continue

            safety = validate_command(intent, per_cmd, ctx)
            if not safety.safe:
                print(f"SKIPPED {f}: {safety.warning}")
                continue

            executor.execute(per_cmd)

        return 0

    # -------- Normal execution --------
    cmd = build_command(intent, result, ctx)
    if not cmd:
        print("ERROR: Unsupported or invalid command")
        return 1

    safety = validate_command(intent, cmd, ctx)
    if not safety.safe:
        if input(f"{safety.warning} Proceed? [y/N]: ").lower() != "y":
            return 1

    executor = CommandExecutor()
    success, output = executor.execute(cmd)

    if not success:
        print(f"ERROR: {output}")
        return 1

    if output:
        print(output)
    if intent in ("CREATE_FILE", "CREATE_DIR"):
        memory.last_path = result.get("path")

    elif intent in ("DELETE_FILE", "DELETE_DIR"):
        memory.last_path = result.get("path")

    elif intent in ("MOVE_FILE", "COPY_FILE", "RENAME_FILE"):
        memory.last_src = result.get("src")
        memory.last_dst = result.get("dst")

    elif intent.startswith("GIT_"):
        memory.last_git_intent = intent
    memory.save()
    return 0


def run():
    sys.exit(main())


if __name__ == "__main__":
    run()
