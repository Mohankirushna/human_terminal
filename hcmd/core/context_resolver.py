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
    t = text.lower()

    # it / that → last path
    if any(p in t for p in (" it", " that")):
        if not result.get("path") and memory.last_path:
            result["path"] = memory.last_path

        if not result.get("src") and memory.last_src:
            result["src"] = memory.last_src

    # there → last directory
    if " there" in t and memory.last_path:
        result["path"] = memory.last_path

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
