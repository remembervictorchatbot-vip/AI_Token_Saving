"""Hot-memory decay audit (v11).

The always-loaded memory/context file is paid on EVERY message - so stale or
bloated entries there are the only savings class that recurs per turn. This
module parses a markdown memory file into entries (## sections or bullet
blocks), scores each by size and staleness signals (dates, "done/complete"
markers, TODO/transient markers), and reports which to demote to an archive,
compress, or keep hot.

Heuristics (deterministic):
  DEMOTE  - marked done/completed/resolved, or carries a date older than
            --stale-days AND no imperative/recall value keywords.
  COMPRESS- entry longer than --max-chars (default 400) but still hot.
  KEEP    - everything else.

Pattern source: memory-architecture skill (hot-cache cap + demotion rules).
"""
import re

DONE_RE = re.compile(
    r"^\s*\*{0,2}(done|completed|fixed|resolved|shipped|merged|closed)\b[:\s*]"
    r"|\b(task|issue|bug|pr|job) (done|completed|closed|merged)\b", re.I | re.M)
LESSON_RE = re.compile(
    r"\b(fixed \d+|repro'd|repro\b|lesson|learned|pitfall|gotcha|never "
    r"|always |BUG:|NOTE:)\b", re.I)
DATE_RE = re.compile(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b")
TRANSIENT_RE = re.compile(r"\b(todo|tbd|wip|next step|in progress)\b", re.I)


def parse_entries(text: str):
    # Split into entries: '## heading' sections, '§'-delimited blocks (Hermes
    # MEMORY.md format), else paragraph blocks.
    if re.search(r"^##\s", text, re.M):
        parts = re.split(r"^(?=##\s)", text, flags=re.M)
        return [(p.splitlines()[0].lstrip("# ").strip() or "(untitled)",
                 p) for p in parts if p.strip()]
    if "\n§\n" in text or text.startswith("§\n"):
        blocks = [b.strip() for b in text.split("\n§\n") if b.strip()]
        return [(b.replace("\n", " ")[:40], b) for b in blocks]
    paras = re.split(r"\n\s*\n", text)
    return [((p.strip().splitlines()[0][:40] if p.strip() else "(blank)"), p)
            for p in paras if p.strip()]


def audit_memory(text: str, max_chars: int = 400, stale_days: int = 30) -> dict:
    import datetime
    now = datetime.date.today()
    actions = []
    total = len(text)
    for title, body in parse_entries(text):
        chars = len(body)
        old_date = None
        for m in DATE_RE.finditer(body):
            ym = re.search(r"(20\d{2})[-/](\d{1,2})", m.group(0))
            if ym:
                try:
                    d = datetime.date(int(ym.group(1)), int(ym.group(2)), 1)
                    age_days = (now - d).days
                    if age_days > stale_days * 6:
                        old_date = age_days
                        break
                except ValueError:
                    continue
        if DONE_RE.search(body) and not TRANSIENT_RE.search(body) \
                and not LESSON_RE.search(body):
            actions.append({"entry": title, "action": "DEMOTE", "chars": chars,
                            "why": "completed marker"})
        elif old_date and chars < max_chars:
            actions.append({"entry": title, "action": "KEEP", "chars": chars,
                            "why": "old date ({}d) but small".format(old_date)})
        elif chars > max_chars:
            actions.append({"entry": title, "action": "COMPRESS",
                            "chars": chars, "why": "{} chars > {}".format(chars, max_chars)})
        else:
            actions.append({"entry": title, "action": "KEEP", "chars": chars,
                            "why": "hot"})
    demote_chars = sum(a["chars"] for a in actions if a["action"] == "DEMOTE")
    compress_chars = sum(a["chars"] for a in actions if a["action"] == "COMPRESS")
    est_saved = demote_chars + int(compress_chars * 0.5)
    return {"entries": actions, "total_chars": total,
            "demotable_pct": round(100.0 * demote_chars / total, 1) if total else 0.0,
            "est_recoverable_pct": round(100.0 * est_saved / total, 1) if total else 0.0}


def format_report(res: dict) -> str:
    lines = ["memory-decay audit ({} chars, {} entries)".format(
        res["total_chars"], len(res["entries"]))]
    for a in res["entries"]:
        lines.append("  [{:>8}] {} ({} chars, {})".format(
            a["action"], a["entry"], a["chars"], a["why"]))
    lines.append("demotable: {}% | est recoverable: {}% per-turn context".format(
        res["demotable_pct"], res["est_recoverable_pct"]))
    return "\n".join(lines)
