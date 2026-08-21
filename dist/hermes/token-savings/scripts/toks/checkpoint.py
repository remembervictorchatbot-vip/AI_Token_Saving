"""Auto-checkpoint before compaction (token-optimizer pattern).

Emits a compact, parseable block capturing the state that must survive a context
compaction or session boundary. This is the backbone of the learning/analysis/
application loop: decisions and lessons are extracted and carried forward instead
of being silently lost when the context is compacted.
"""
import re

SECTIONS = [
    "Active task",
    "Decisions",
    "Modified files",
    "Open questions",
    "Next steps",
    "Lessons to carry",
]


def emit_checkpoint(state: dict) -> str:
    lines = ["<!-- CHECKPOINT -->", "## Session Checkpoint"]
    for s in SECTIONS:
        val = state.get(s, "")
        if isinstance(val, list):
            val = "\n".join(f"- {v}" for v in val) or "- (none)"
        lines.append(f"**{s}:** {val if val else '(none)'}")
    lines.append("<!-- /CHECKPOINT -->")
    return "\n".join(lines)


def parse_checkpoint(text: str) -> dict:
    m = re.search(r"<!-- CHECKPOINT -->(.*?)<!-- /CHECKPOINT -->", text, re.DOTALL)
    body = m.group(1) if m else text
    out = {}
    pattern = r"\*\*(.+?):\*\*\s*(.*?)(?=\n\*\*(?:.+?):\*\*|\Z)"
    for mm in re.finditer(pattern, body, re.DOTALL):
        out[mm.group(1).strip()] = mm.group(2).strip()
    return out
