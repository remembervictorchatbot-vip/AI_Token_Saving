"""Session autopilot (v10): the self-enforcing loop in one command.

Given a session transcript, runs the whole discipline automatically:
  input-meter  -> what the session actually cost (input side)
  audit-session-> which standing rules were violated (flow side)
  output-gate  -> whether the last reply passes O-1..O-6 (output side)
and emits a compact NEXT-TURN DIRECTIVES block: what to stop, what to apply,
and the continuity hint. The agent reads it FIRST on the next turn.
Pure stdlib, deterministic, recommend-only.
"""
from toks import audit, input_meter, output


def autopilot(text: str, task_type: str = "chat_reply") -> dict:
    """Meter + audit + gate a session transcript in one pass."""
    meter = input_meter.meter(text)
    findings = audit.audit_session(text)
    blocks = audit._blocks(text)
    last = blocks[-1] if blocks else ""
    if last:
        gate = output.gate_reply(last, task_type)
    else:
        gate = {"pass": True, "issues": [], "lines": 0, "ceiling": 0}
    return {"meter": meter, "findings": findings, "gate": gate}


def format_directives(r: dict) -> str:
    """NEXT-TURN DIRECTIVES: what the agent must apply next turn."""
    lines = ["[autopilot] NEXT-TURN DIRECTIVES (read first)"]
    m = r["meter"]
    lines.append("  input : ~{tok:,} tok sent; {rtok:,} tok repeat waste ({rp}%)".format(
        tok=m["actual_tok"], rtok=m["repeat_tok"], rp=m["recoverable_pct"]))
    if r["findings"]:
        lines.append("  flow  : {} violation(s) - apply fixes now:".format(len(r["findings"])))
        for f in r["findings"][:5]:
            lines.append("    - [{}] {}".format(f["rule"], f["detail"]))
    else:
        lines.append("  flow  : clean")
    g = r["gate"]
    if g["pass"]:
        lines.append("  output: last reply passes O-1..O-6 ({} lines, ceiling {})".format(g["lines"], g["ceiling"]))
    else:
        lines.append("  output: last reply FAILS the O-gate:")
        for i in g["issues"]:
            lines.append("    - " + i)
    lines.append("  continuity: run the checkpoint --auto command on open work before ending the turn")
    return "\n".join(lines)