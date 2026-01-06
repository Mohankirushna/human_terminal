import os
import fnmatch
from typing import List
from hcmd.core.context import SystemContext


def resolve_pattern(pattern: str, ctx: SystemContext) -> List[str]:
    """
    Convert a pattern (*.txt, *.csv, etc) into real file paths
    """
    matches = []

    for root, _, files in os.walk(ctx.cwd):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                matches.append(os.path.join(root, name))

    return matches
