import os
from hcmd.constants import OS
from hcmd.core.context import SystemContext


def build_rollback(intent: str, step: dict, ctx: SystemContext) -> str | None:
    os_type = ctx.os_type

    # -------- FILE SYSTEM --------
    if intent == "CREATE_FILE":
        path = step.get("path")
        if not path:
            return None
        return (
            f'del "{path}"'
            if os_type == OS.WINDOWS
            else f'rm "{path}"'
        )

    if intent == "CREATE_DIR":
        path = step.get("path")
        if not path:
            return None
        return (
            f'Remove-Item -Recurse -Force "{path}"'
            if os_type == OS.WINDOWS
            else f'rm -r "{path}"'
        )

    if intent == "DELETE_FILE":
        # ⚠️ destructive → cannot rollback safely
        return None

    if intent == "DELETE_DIR":
        return None

    if intent == "MOVE_FILE":
        src = step.get("src")
        dst = step.get("dst")

        if not src or not dst:
            return None

        src = os.path.abspath(src)
        dst = os.path.abspath(dst)

        # actual moved file path
        moved_file = (
            os.path.join(dst, os.path.basename(src))
            if os.path.isdir(dst)
            else dst
        )

        original_location = os.path.dirname(src)

        if os_type == OS.WINDOWS:
            return f'Move-Item "{moved_file}" "{original_location}"'
        else:
            return f'mv "{moved_file}" "{original_location}"'
    
    if intent == "RENAME_FILE":
        src = step.get("src")
        dst = step.get("dst")
        if not src or not dst:
            return None
        return (
            f'Rename-Item "{dst}" "{src}"'
            if os_type == OS.WINDOWS
            else f'mv "{dst}" "{src}"'
        )

    # -------- GIT --------
    if intent == "GIT_ADD":
        path = step.get("path")
        if not path:
            return None
        return f'git reset "{path}"'

    if intent == "GIT_CHECKOUT":
        # risky, do not auto rollback
        return None

    if intent == "GIT_RESET":
        return "git reset --hard HEAD@{1}"

    # -------- UNSUPPORTED --------
    return None
