import sys
import os

from hcmd.core.executor import CommandExecutor
from hcmd.core.context_resolver import resolve_context
from hcmd.core.nlp import interpret_plan
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
# Command builder
# --------------------------------------------------
def build_command(intent: str, data: dict, ctx: SystemContext) -> str | None:
    os_type = ctx.os_type

    # ---------- BASIC ----------
    if intent == "LIST_FILES":
        return "Get-ChildItem" if os_type == OS.WINDOWS else "ls -la"

    if intent == "PWD":
        return "Get-Location" if os_type == OS.WINDOWS else "pwd"

    if intent == "NAVIGATION":
        path = normalize_path(data.get("path"), ctx)
        return f'cd "{path}"' if path else None

    # ---------- FILE OPS ----------
    if intent in ("MOVE_FILE", "COPY_FILE"):
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        if intent == "MOVE_FILE":
            return f'Move-Item "{src}" "{dst}"' if os_type == OS.WINDOWS else f'mv "{src}" "{dst}"'
        else:
            return f'Copy-Item "{src}" "{dst}"' if os_type == OS.WINDOWS else f'cp "{src}" "{dst}"'

    if intent == "CREATE_FILE":
        name = data.get("path")
        return f'New-Item -ItemType File "{name}"' if os_type == OS.WINDOWS else f'touch "{name}"'

    if intent == "CREATE_DIR":
        name = data.get("path")
        return f'New-Item -ItemType Directory "{name}"' if os_type == OS.WINDOWS else f'mkdir "{name}"'

    if intent == "DELETE_FILE":
        target = normalize_path(data.get("path"), ctx)
        return f'del "{target}"' if os_type == OS.WINDOWS else f'rm "{target}"'

    if intent == "DELETE_DIR":
        target = normalize_path(data.get("path"), ctx)
        return f'Remove-Item -Recurse -Force "{target}"' if os_type == OS.WINDOWS else f'rm -r "{target}"'

    if intent == "RENAME_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        return f'Rename-Item "{src}" "{dst}"' if os_type == OS.WINDOWS else f'mv "{src}" "{dst}"'

    # ---------- SYSTEM ----------
    if intent == "SYSTEM_INFO":
        return "systeminfo" if os_type == OS.WINDOWS else "uname -a"

    if intent == "PROCESS_LIST":
        return "tasklist" if os_type == OS.WINDOWS else "ps aux"

    if intent == "NETWORK_INFO":
        return "ipconfig" if os_type == OS.WINDOWS else "ifconfig"

    if intent == "PROCESS_KILL":
        target = data.get("target")
        if not target:
            return None
        if os_type == OS.WINDOWS:
            return f'taskkill /PID {target} /F' if target.isdigit() else f'taskkill /IM {target}.exe /F'
        return f'kill {target}' if target.isdigit() else f'killall {target}'

    # ---------- GIT ----------
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
    if intent == "GIT_ADD":
        return f'git add "{data.get("path")}"'
    if intent == "GIT_CHECKOUT":
        return f'git checkout "{data.get("branch")}"'
    if intent == "GIT_CLONE":
        return f'git clone "{data.get("repo")}"'

    return None


# --------------------------------------------------
# MAIN (PHASE 9)
# --------------------------------------------------
def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: hcmd <command>")
        return 1

    text = " ".join(sys.argv[1:])
    ctx = resolve_context()

    plan = interpret_plan(text)
    if not plan.get("ok"):
        print(f"ERROR: {plan.get('reason')}")
        return 1

    steps = plan["steps"]

    # ----- Show plan -----
    if len(steps) > 1:
        print("I will execute the following steps:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step['intent']}")
        if input("Proceed? [y/N]: ").lower() != "y":
            return 1

    executor = CommandExecutor()

    # ----- Execute steps -----
    for step in steps:
        intent = step["intent"]

        clarification = detect_ambiguity(intent, step, ctx)
        if isinstance(clarification, ClarificationRequest):
            if not clarification.options:
                print(f"ERROR: {clarification.reason}")
                return 1
            print(f"CLARIFICATION REQUIRED: {clarification.reason}")
            for i, opt in enumerate(clarification.options, 1):
                print(f"{i}) {opt}")
            idx = int(input("Select option number: ")) - 1
            step["path"] = clarification.options[idx]

        if "pattern" in step:
            files = resolve_pattern(step["pattern"], ctx)
            for f in files:
                cmd = build_command(intent, {**step, "path": f}, ctx)
                executor.execute(cmd)
            continue

        cmd = build_command(intent, step, ctx)
        if not cmd:
            print("ERROR: Unsupported command")
            return 1

        safety = validate_command(intent, cmd, ctx)
        if not safety.safe:
            if input(f"{safety.warning} Proceed? [y/N]: ").lower() != "y":
                return 1

        success, output = executor.execute(cmd)
        if not success:
            print(f"ERROR: {output}")
            return 1
        if output:
            print(output)

        # ----- Memory -----
        if intent in ("CREATE_FILE", "DELETE_FILE", "CREATE_DIR", "DELETE_DIR"):
            memory.last_path = step.get("path") or memory.last_path
        if intent in ("MOVE_FILE", "COPY_FILE", "RENAME_FILE"):
            memory.last_src = step.get("src") or memory.last_src
            memory.last_dst = step.get("dst") or memory.last_dst
        if intent.startswith("GIT_"):
            memory.last_git_intent = intent

    memory.save()
    return 0


def run():
    sys.exit(main())


if __name__ == "__main__":
    run()
import sys
import os

from hcmd.core.executor import CommandExecutor
from hcmd.core.context_resolver import resolve_context
from hcmd.core.nlp import interpret_plan
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
# Command builder
# --------------------------------------------------
def build_command(intent: str, data: dict, ctx: SystemContext) -> str | None:
    os_type = ctx.os_type

    # ---------- BASIC ----------
    if intent == "LIST_FILES":
        return "Get-ChildItem" if os_type == OS.WINDOWS else "ls -la"

    if intent == "PWD":
        return "Get-Location" if os_type == OS.WINDOWS else "pwd"

    if intent == "NAVIGATION":
        path = normalize_path(data.get("path"), ctx)
        return f'cd "{path}"' if path else None

    # ---------- FILE OPS ----------
    if intent in ("MOVE_FILE", "COPY_FILE"):
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        if not src or not dst:
            return None
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        if intent == "MOVE_FILE":
            return f'Move-Item "{src}" "{dst}"' if os_type == OS.WINDOWS else f'mv "{src}" "{dst}"'
        else:
            return f'Copy-Item "{src}" "{dst}"' if os_type == OS.WINDOWS else f'cp "{src}" "{dst}"'

    if intent == "CREATE_FILE":
        name = data.get("path")
        return f'New-Item -ItemType File "{name}"' if os_type == OS.WINDOWS else f'touch "{name}"'

    if intent == "CREATE_DIR":
        name = data.get("path")
        return f'New-Item -ItemType Directory "{name}"' if os_type == OS.WINDOWS else f'mkdir "{name}"'

    if intent == "DELETE_FILE":
        target = normalize_path(data.get("path"), ctx)
        return f'del "{target}"' if os_type == OS.WINDOWS else f'rm "{target}"'

    if intent == "DELETE_DIR":
        target = normalize_path(data.get("path"), ctx)
        return f'Remove-Item -Recurse -Force "{target}"' if os_type == OS.WINDOWS else f'rm -r "{target}"'

    if intent == "RENAME_FILE":
        src = normalize_path(data.get("src"), ctx)
        dst = normalize_path(data.get("dst"), ctx)
        return f'Rename-Item "{src}" "{dst}"' if os_type == OS.WINDOWS else f'mv "{src}" "{dst}"'

    # ---------- SYSTEM ----------
    if intent == "SYSTEM_INFO":
        return "systeminfo" if os_type == OS.WINDOWS else "uname -a"

    if intent == "PROCESS_LIST":
        return "tasklist" if os_type == OS.WINDOWS else "ps aux"

    if intent == "NETWORK_INFO":
        return "ipconfig" if os_type == OS.WINDOWS else "ifconfig"

    if intent == "PROCESS_KILL":
        target = data.get("target")
        if not target:
            return None
        if os_type == OS.WINDOWS:
            return f'taskkill /PID {target} /F' if target.isdigit() else f'taskkill /IM {target}.exe /F'
        return f'kill {target}' if target.isdigit() else f'killall {target}'

    # ---------- GIT ----------
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
    if intent == "GIT_ADD":
        return f'git add "{data.get("path")}"'
    if intent == "GIT_CHECKOUT":
        return f'git checkout "{data.get("branch")}"'
    if intent == "GIT_CLONE":
        return f'git clone "{data.get("repo")}"'
    if intent == "GIT_REPO_STATUS":
        return "git rev-parse --is-inside-work-tree"
    return None


# --------------------------------------------------
# MAIN (PHASE 9)
# --------------------------------------------------
def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: hcmd <command>")
        return 1

    text = " ".join(sys.argv[1:])
    ctx = resolve_context()

    plan = interpret_plan(text)
    if not plan.get("ok"):
        print(f"ERROR: {plan.get('reason')}")
        return 1

    steps = plan["steps"]

    # ----- Show plan -----
    if len(steps) > 1:
        print("I will execute the following steps:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step['intent']}")
        if input("Proceed? [y/N]: ").lower() != "y":
            return 1

    executor = CommandExecutor()

    # ----- Execute steps -----
    for step in steps:
        intent = step["intent"]

        clarification = detect_ambiguity(intent, step, ctx)
        if isinstance(clarification, ClarificationRequest):
            if not clarification.options:
                print(f"ERROR: {clarification.reason}")
                return 1
            print(f"CLARIFICATION REQUIRED: {clarification.reason}")
            for i, opt in enumerate(clarification.options, 1):
                print(f"{i}) {opt}")
            idx = int(input("Select option number: ")) - 1
            step["path"] = clarification.options[idx]

        if "pattern" in step:
            files = resolve_pattern(step["pattern"], ctx)
            for f in files:
                cmd = build_command(intent, {**step, "path": f}, ctx)
                executor.execute(cmd)
            continue

        cmd = build_command(intent, step, ctx)
        if not cmd:
            print("ERROR: Unsupported command")
            return 1

        safety = validate_command(intent, cmd, ctx)
        if not safety.safe:
            if input(f"{safety.warning} Proceed? [y/N]: ").lower() != "y":
                return 1

        success, output = executor.execute(cmd)
        if not success:
            print(f"ERROR: {output}")
            return 1
        if output:
            print(output)

        # ----- Memory -----
        if intent in ("CREATE_FILE", "DELETE_FILE", "CREATE_DIR", "DELETE_DIR"):
            memory.last_path = step.get("path") or memory.last_path
        if intent in ("MOVE_FILE", "COPY_FILE", "RENAME_FILE"):
            memory.last_src = step.get("src") or memory.last_src
            memory.last_dst = step.get("dst") or memory.last_dst
        if intent.startswith("GIT_"):
            memory.last_git_intent = intent

    memory.save()
    return 0


def run():
    sys.exit(main())


if __name__ == "__main__":
    run()
