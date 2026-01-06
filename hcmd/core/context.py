import os
from dataclasses import dataclass, field
from typing import Optional, List
from hcmd.constants import OS


@dataclass
class SystemContext:
    os_type: OS
    cwd: str

    is_git_repo: bool = False
    git_branch: Optional[str] = None
    git_dirty: bool = False

    docker_available: bool = False
    docker_running: bool = False
    docker_containers: List[str] = field(default_factory=list)


def empty_context(os_type: OS) -> SystemContext:
    return SystemContext(
        os_type=os_type,
        cwd=os.getcwd()
    )
