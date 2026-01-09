import os
import subprocess
from hcmd.constants import OS
from hcmd.core.detector import get_os
from hcmd.core.context import SystemContext


def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return p.returncode, p.stdout.strip()
    except Exception:
        return 1, ""


def _resolve_git(ctx: SystemContext) -> None:
    code, _ = _run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ctx.cwd
    )
    if code != 0:
        return

    ctx.is_git_repo = True

    code, branch = _run(
        ["git", "branch", "--show-current"],
        cwd=ctx.cwd
    )
    if code == 0 and branch:
        ctx.git_branch = branch

    code, status = _run(
        ["git", "status", "--porcelain"],
        cwd=ctx.cwd
    )
    if code == 0:
        ctx.git_dirty = bool(status)


def _resolve_docker(ctx: SystemContext) -> None:
    code, _ = _run(["docker", "info"])
    if code != 0:
        ctx.docker_available = False
        ctx.docker_running = False
        return

    ctx.docker_available = True
    ctx.docker_running = True

    code, out = _run(["docker", "ps", "--format", "{{.Names}}"])
    if code == 0 and out:
        ctx.docker_containers = out.splitlines()

def resolve_pronouns(text: str, result: dict, memory):
    """
    Deterministic pronoun resolution.
    This happens AFTER intent detection but BEFORE execution.
    """

    tokens = text.lower().split()

    def get_recent(idx: int):
        if len(memory.recent_objects) > idx:
            return memory.recent_objects[-(idx + 1)]
        return None

    # --- it / this → most recent ---
    if any(tok in ("it", "this") for tok in tokens):
        resolved = get_recent(0)
        if resolved:
            result.setdefault("path", resolved)
            result.setdefault("src", resolved)
            result["from_pronoun"] = True

    # --- that → previous ---
    if "that" in tokens:
        resolved = get_recent(1)
        if resolved:
            result.setdefault("path", resolved)
            result.setdefault("src", resolved)
            result["from_pronoun"] = True

    # --- there → last directory ---
    if "there" in tokens and memory.last_path:
        result.setdefault("path", memory.last_path)
        result["from_pronoun"] = True

    return result


def resolve_context() -> SystemContext:
    os_type = get_os()

    ctx = SystemContext(
        os_type=os_type,
        cwd=os.getcwd()
    )

    _resolve_git(ctx)
    _resolve_docker(ctx)

    return ctx
