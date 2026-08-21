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


def auto_state(text: str) -> dict:
    """Heuristically extract checkpoint state from a transcript (v10).

    No manual fields needed: active task = first substantive line; next steps
    = lines starting with todo/next; decisions = lines starting with decided.
    Deterministic and testable; refine heuristics as patterns appear.
    """
    active, decisions, next_steps = "", [], []
    for ln in text.splitlines():
        s = ln.strip().lstrip("-*").strip()
        low = s.lower()
        if low.startswith(("todo:", "next:", "next step", "next steps")):
            next_steps.append(s)
        elif low.startswith(("decided", "decision:", "decision ->")):
            decisions.append(s)
    for ln in text.splitlines():
        s = ln.strip()
        if len(s) > 20 and not s.startswith(("#", "[", "```", "|")):
            active = s[:120]
            break
    return {"Active task": active or "(none)",
            "Decisions": decisions, "Next steps": next_steps}


def parse_checkpoint(text: str) -> dict:
    m = re.search(r"<!-- CHECKPOINT -->(.*?)<!-- /CHECKPOINT -->", text, re.DOTALL)
    body = m.group(1) if m else text
    out = {}
    pattern = r"\*\*(.+?):\*\*\s*(.*?)(?=\n\*\*(?:.+?):\*\*|\Z)"
    for mm in re.finditer(pattern, body, re.DOTALL):
        out[mm.group(1).strip()] = mm.group(2).strip()
    return out
