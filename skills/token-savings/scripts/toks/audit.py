"""Session self-audit - closes the loop on the behavioral rules (new, v8).

Scans a session transcript (paste or file) and flags standing-rule violations
with deterministic heuristics:
  1. re-reads        : identical content blocks appearing >= 2 times (dedup)
  2. prose bloat     : messages >40 lines with no code fence or table (A1/O-5)
  3. loop            : the same command line repeated >= 3 times (A4)
  4. unvalidated JSON: lines that look like JSON but fail to parse (O-1/O-6)
Recommend-only, like toolaudit: it reports; the agent fixes. Pure stdlib.
"""
import json


def _blocks(text: str):
    """Split transcript into content blocks (paragraphs)."""
    return [b.strip() for b in text.split("\n\n") if b.strip()]


def audit_session(text: str) -> list:
    """Return a list of {rule, line, detail} findings. Empty = clean."""
    findings = []
    blocks = _blocks(text)

    # 1. re-reads: identical large blocks repeated
    seen = {}
    for i, b in enumerate(blocks):
        if len(b) > 200:
            key = json.dumps(b[:200], ensure_ascii=False)
            if key in seen:
                findings.append({
                    "rule": "re-read",
                    "line": i + 1,
                    "detail": f"identical {len(b)}-char block repeated (dedup: use a ref)",
                })
            else:
                seen[key] = i

    # 2. prose bloat: long paragraphs with no structure
    for i, b in enumerate(blocks):
        n = len(b.splitlines())
        if n > 40 and "```" not in b and "|" not in b:
            findings.append({
                    "rule": "prose-bloat",
                    "line": i + 1,
                    "detail": f"{n}-line prose block with no table/code fence (A1/O-5)",
                })

    # 3. loop: identical command lines repeated >= 3 times
    counts = {}
    for i, ln in enumerate(text.splitlines(), 1):
        s = ln.strip()
        if s and not s.startswith("#"):
            counts.setdefault(s, []).append(i)
    for cmd, lines in counts.items():
        if len(lines) >= 3:
            findings.append({
                    "rule": "loop",
                    "line": lines[0],
                    "detail": f"same command {len(lines)}x: {cmd[:60]}",
                })

    # 4. unvalidated JSON emit
    for i, ln in enumerate(text.splitlines(), 1):
        s = ln.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                json.loads(s)
            except Exception:
                findings.append({
                    "rule": "json",
                    "line": i,
                    "detail": f"looks like JSON but does not parse: {s[:60]}",
                })
    return findings


def format_report(findings: list) -> str:
    """Human-readable audit report."""
    if not findings:
        return "Session audit: CLEAN (no standing-rule violations)"
    lines = ["Session audit: {} finding(s)".format(len(findings))]
    for f in findings:
        lines.append("  [{}] L{}: {}".format(f["rule"], f["line"], f["detail"]))
    return "\n".join(lines)