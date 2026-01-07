import os
import fnmatch
from typing import List
from hcmd.core.context import SystemContext


def resolve_pattern(pattern, ctx: SystemContext) -> List[str]:
    """
    Convert a pattern (*.txt, *.csv, etc) into real file paths.
    Defensive against malformed or structured patterns.
    """

    # -------------------------
    # Normalize pattern
    # -------------------------
    if isinstance(pattern, dict):
        pattern = pattern.get("pattern")

    if not isinstance(pattern, str) or not pattern:
        return []

    matches: List[str] = []

    # -------------------------
    # Search from cwd downward
    # -------------------------
    for root, _, files in os.walk(ctx.cwd):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                matches.append(os.path.join(root, name))

    return matches
