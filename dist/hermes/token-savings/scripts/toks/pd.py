"""Progressive-disclosure prompt audit (v11).

Classifies sections of an agent instruction file (AGENTS.md, SKILL.md, system
prompt) into Layer 1 (always loaded: mandates, security, operational rules)
and Layer 2 (extract to reference: history, enumerations, big tables,
checklists), then reports estimated base-prompt savings and a pointer-contract
check. Pattern source: progressive-disclosure-pattern skill (two-layer model).

Layer 2 criteria (any hit -> extract):
  1. historical narrative   ("this rule exists because ...", "we once ...")
  2. full enumeration       (5+ list items under one heading)
  3. config/reference table (markdown table with 4+ rows)
  4. checklist of rare ops  (env vars, file inventories)

Layer 1 stays inline:
  - security words (secret, credential, injection) - NEVER defer
  - mandatory/imperative rules (MUST, ALWAYS, NEVER at line start)
  - short operational commands

Deterministic, pure stdlib.
"""
import re


SECURITY_RE = re.compile(
    r"\b(secret|credential|token|api[- ]?key|password|injection|override)\b", re.I)
MANDATE_RE = re.compile(r"\b(MUST|ALWAYS|NEVER|Mandatory)\b")
HISTORY_RE = re.compile(
    r"\b(because we|this (rule|exists) (because|after)|we (once|used to)|"
    r"histor(y|ically)|that caused|previously (caused|failed))\b", re.I)


def _sections(text: str):
    """Split markdown into (title, body) sections by ATX headings."""
    secs, cur_title, cur = [], "(preamble)", []
    for ln in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            if cur or cur_title != "(preamble)":
                secs.append((cur_title, "\n".join(cur)))
            cur_title, cur = m.group(2).strip(), [ln]
        else:
            cur.append(ln)
    secs.append((cur_title, "\n".join(cur)))
    return [(t, b) for t, b in secs if b.strip()]


def _classify(title: str, body: str) -> str:
    """Return 'L1' (keep inline) or 'L2' (extract to reference)."""
    blob = title + "\n" + body
    # Hard L1: security content never defers entirely.
    if SECURITY_RE.search(blob) and MANDATE_RE.search(blob):
        return "L1"
    lines = [ln for ln in body.splitlines() if ln.strip()]
    # Table with 4+ data rows -> reference material.
    table_rows = sum(1 for ln in lines if ln.strip().startswith("|") and "---" not in ln) - 1
    if table_rows >= 4:
        return "L2"
    # Historical narrative -> reference.
    if HISTORY_RE.search(blob):
        return "L2"
    # Full enumeration: 6+ bullet items under one section -> extract summary.
    bullets = sum(1 for ln in lines if re.match(r"\s*([-*]|\d+\.)\s", ln))
    if bullets >= 6 and len(lines) > 10:
        return "L2"
    # Long low-density prose (>40 lines, no mandate/security) -> reference.
    if len(lines) > 40 and not MANDATE_RE.search(blob) and not SECURITY_RE.search(blob):
        return "L2"
    return "L1"


def audit_prompt(text: str, budget_tokens: int = 30000) -> dict:
    """Classify each section; return layer map + estimated savings."""
    def est(s):
        return max(1, len(s) // 4)
    total, l1_chars, l2 = est(text), 0, []
    for title, body in _sections(text):
        if _classify(title, body) == "L2":
            l2.append({"section": title, "chars": len(body)})
        else:
            l1_chars += est(body)
    kept = l1_chars + est("\n".join(
        "> pointer: see reference for: " + s["section"] for s in l2))
    saved_pct = round(100.0 * (total - kept) / total, 1) if total else 0.0
    return {
        "total_tok_est": total,
        "l1_tok_est": l1_chars,
        "l2_sections": l2,
        "with_pointers_tok_est": kept,
        "saved_pct": saved_pct,
        "within_budget": total <= budget_tokens,
        "budget_tokens": budget_tokens,
    }


def format_report(res: dict) -> str:
    lines = [
        "progressive-disclosure audit",
        "  base prompt: {} tok est (budget {})".format(
            res["total_tok_est"], res["budget_tokens"]),
        "  within budget: {}".format(res["within_budget"]),
        "  L2 (extract to reference): {} sections".format(len(res["l2_sections"])),
    ]
    for s in res["l2_sections"]:
        lines.append("    - {} ({} chars)".format(s["section"], s["chars"]))
    lines.append("  after extraction + pointers: ~{} tok ({}% saved)".format(
        res["with_pointers_tok_est"], res["saved_pct"]))
    return "\n".join(lines)
