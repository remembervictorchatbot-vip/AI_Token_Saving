"""Output-side economics (v6, O-1..O-5).

Validated from the 2026 output-token techniques through the layer filter:
only what we control behaviorally. API params (max_tokens, stop sequences,
model routing) are out of our layer and rejected. Pure stdlib, provider-agnostic.

- budget(task_type)     -> O-2 length ceiling (lines) for our own replies
- valid_json(text)      -> O-1 output quality gate: verify before emitting
- table_lines(...)      -> O-1 header-once table emitter (TOON principle,
                           no custom format, no downstream risk)
- AnswerCache           -> O-4 session answer-once cache with staleness guard
                           (in-memory; deterministic facts only)

Behavioral rules, not independently benchmarked in our environment.
"""
import hashlib
import json

# O-2: task-type -> max output in lines (or "data" for machine-consumed).
BUDGETS = {
    "verdict": 1,
    "classification": 3,
    "chat_reply": 15,
    "summary": 6,        # ~1 paragraph
    "analysis": 30,
    "report": 70,
    "code_snippet": 150,
    "data_only": 0,      # data, zero prose
}


def budget(task_type: str) -> int:
    """Return the O-2 ceiling for a task type (lines). Unknown -> chat_reply."""
    return BUDGETS.get(task_type, BUDGETS["chat_reply"])


def valid_json(text: str) -> bool:
    """O-1 output quality gate: does this parse as JSON before we emit it?"""
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def table_lines(header: list, rows: list) -> str:
    """O-1 header-once table (TOON principle, plain text): declare columns once,
    then stream rows. More token-compact than repeated-key JSON for uniform rows.
    """
    if not header:
        return ""
    rows = [list(r) for r in rows]
    ncols = len(header)
    rows = [r[:ncols] + [""] * (ncols - len(r)) for r in rows]
    width = []
    for i, h in enumerate(header):
        w = len(str(h))
        for r in rows:
            if i < len(r):
                w = max(w, len(str(r[i])))
        width.append(w)

    def fmt(row):
        return " | ".join(str(row[i]).ljust(width[i]) for i in range(ncols))

    sep = "-+-".join("-" * w for w in width)
    return "\n".join([fmt(header), sep] + [fmt(r) for r in rows])


class AnswerCache:
    """O-4 session answer-once cache.

    key = sha256(query + context). get() returns the previous answer for the
    exact same query+context; if inputs changed, call with fresh=True to force
    regeneration (staleness guard). In-memory, session-scoped - never persisted,
    so a stale answer can never leak across sessions.
    """

    def __init__(self):
        self._store = {}

    @staticmethod
    def _key(query: str, context: str) -> str:
        return hashlib.sha256(f"{query}\x00{context}".encode("utf-8")).hexdigest()[:16]

    def get(self, query: str, context: str = "", fresh: bool = False):
        """Return cached answer, or None on miss (or when fresh forces regen)."""
        if fresh:
            return None
        return self._store.get(self._key(query, context))

    def put(self, query: str, context: str, answer: str) -> str:
        """Store an answer; returns the cache key for debugging."""
        k = self._key(query, context)
        self._store[k] = answer
        return k

    def stats(self) -> dict:
        return {"entries": len(self._store)}


# --- O-1..O-6 reply gate (v10): self-enforcing output check before emit ---

FLUFF_PATTERNS = (
    "let me know if you have any other",
    "let me know if you need",
    "i hope this helps",
    "hope this helps",
    "feel free to reach out",
    "best regards",
    "thanks for asking",
)


def gate_reply(text: str, task_type: str = "chat_reply") -> dict:
    """Run O-1..O-6 checks on a reply BEFORE finalizing it.

    Returns {'pass': bool, 'issues': [...], 'lines': n, 'ceiling': N}.
    - O-2: line count vs the task-type ceiling
    - O-5: trailing filler (skipped for chat replies, where politeness is normal)
    - O-1/O-6: JSON-looking output must parse; code fences must be balanced
    """
    issues = []
    lines = text.splitlines()
    n = len(lines)
    ceiling = budget(task_type)
    if ceiling and n > ceiling:
        issues.append("O-2: {} lines exceeds ceiling {} for {}".format(n, ceiling, task_type))
    if task_type != "chat_reply":
        low = text.strip().lower()
        for pat in FLUFF_PATTERNS:
            if pat in low:
                issues.append("O-5: trailing filler matched: {!r}".format(pat))
                break
    if text.lstrip()[:1] in "[{":
        if not valid_json(text):
            issues.append("O-1/O-6: looks like JSON but does not parse")
    fences = text.count("```")
    if fences % 2:
        issues.append("O-6: unbalanced code fences")
    return {"pass": len(issues) == 0, "issues": issues, "lines": n, "ceiling": ceiling}
