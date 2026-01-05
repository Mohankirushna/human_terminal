from dataclasses import dataclass
from hcmd.core.context import SystemContext

@dataclass
class SafetyResult:
    safe: bool
    warning: str | None = None

import os

DANGEROUS_PATHS = {
    "/",
    "/usr",
    "/bin",
    "/etc",
    ".git",
}

def validate_command(intent: str, cmd: str, ctx: SystemContext) -> SafetyResult:
    if intent in ("DELETE_FILE", "MOVE_FILE", "COPY_FILE"):
        for p in DANGEROUS_PATHS:
            if p in cmd:
                return SafetyResult(
                    safe=False,
                    warning=f"Command touches protected path: {p}"
                )

    if intent == "DELETE_FILE":
        return SafetyResult(
            safe=False,
            warning="Delete operations can be destructive"
        )

    if intent.startswith("GIT_") and not ctx.is_git_repo:
        return SafetyResult(
            safe=False,
            warning="Git command outside a repository"
        )

    if intent == "NAVIGATION" and ctx.cwd == "/":
        return SafetyResult(
            safe=False,
            warning="Navigating from root directory"
        )

    return SafetyResult(safe=True)
