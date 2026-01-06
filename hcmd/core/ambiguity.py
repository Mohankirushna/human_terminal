import os
from dataclasses import dataclass
from typing import List, Optional
from hcmd.core.context import SystemContext


@dataclass
class ClarificationRequest:
    reason: str
    options: List[str]


def detect_ambiguity(intent: str, data: dict, ctx: SystemContext) -> Optional[ClarificationRequest]:
    """
    Returns ClarificationRequest if ambiguity exists, else None
    """

    # ---------- DELETE / READ / RENAME ----------
    if intent in ("DELETE_FILE", "READ_FILE", "RENAME_FILE"):
        target = data.get("path") or data.get("src")
        if not target:
            return ClarificationRequest(
                reason="No file specified",
                options=[]
            )

        matches = []

        for root, _, files in os.walk(ctx.cwd):
            if target in files:
                matches.append(os.path.join(root, target))

        if len(matches) == 0:
            return ClarificationRequest(
                reason=f"No file named '{target}' found",
                options=[]
            )

        if len(matches) > 1:
            return ClarificationRequest(
                reason=f"Multiple files named '{target}' found",
                options=matches
            )

        data["path"] = matches[0]
        data["src"] = matches[0]

    # ---------- MOVE / COPY ----------
    if intent in ("MOVE_FILE", "COPY_FILE"):
        src = data.get("src")
        if not src:
            return ClarificationRequest(
                reason="No source file specified",
                options=[]
            )

        matches = []
        for root, _, files in os.walk(ctx.cwd):
            if src in files:
                matches.append(os.path.join(root, src))

        if len(matches) == 0:
            return ClarificationRequest(
                reason=f"No file named '{src}' found",
                options=[]
            )

        if len(matches) > 1:
            return ClarificationRequest(
                reason=f"Multiple files named '{src}' found",
                options=matches
            )

        data["src"] = matches[0]

    # ---------- NAVIGATION ----------
    if intent == "NAVIGATION":
        path = data.get("path")
        if not path:
            return ClarificationRequest(
                reason="No destination specified",
                options=[]
            )

        candidates = []
        for root, dirs, _ in os.walk(ctx.cwd):
            if path in dirs:
                candidates.append(os.path.join(root, path))

        if len(candidates) > 1:
            return ClarificationRequest(
                reason=f"Multiple directories named '{path}' found",
                options=candidates
            )

        if len(candidates) == 1:
            data["path"] = candidates[0]

    return None
