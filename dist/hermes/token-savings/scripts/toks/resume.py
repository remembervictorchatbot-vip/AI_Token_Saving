"""Durable session checkpoint (RESUME.md) — survives compaction / turn boundaries.

The loop's continuity promise (decisions + lessons carried forward) only holds if
the checkpoint is written to a *file the next turn can read*, not buried in a chat
that may be compacted. Compaction is not observable to the agent, so "emit before
compaction" never fires. The fix: write a durable file at the end of every turn
where work is open. This helper reads/writes `.workbuddy/RESUME.md`.
"""
import os

from toks import checkpoint

DEFAULT_PATH = os.path.join(".workbuddy", "RESUME.md")


def write_resume(state: dict, path: str = DEFAULT_PATH) -> str:
    """Write the checkpoint block to `path`. Returns the path written."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(checkpoint.emit_checkpoint(state) + "\n")
    return path


def read_resume(path: str = DEFAULT_PATH) -> dict:
    """Parse the checkpoint from `path`. Returns {} if missing."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return checkpoint.parse_checkpoint(f.read())


def has_open_work(path: str = DEFAULT_PATH) -> bool:
    """True if a resume file exists and records an active task or next steps."""
    data = read_resume(path)
    if not data:
        return False
    active = data.get("Active task", "")
    nxt = data.get("Next steps", "")
    return (bool(active) and active != "(none)") or (bool(nxt) and nxt != "(none)")
