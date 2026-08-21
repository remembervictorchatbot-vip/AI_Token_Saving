"""Token estimation + quality gate (token-optimizer quality scoring, simplified).

The quality gate is the guarantee that compression never drops protected content.
Entropy is intentionally NOT an auto-delete: it is a diagnostic only.
"""
import re

PROTECT_OPEN = "[[KEEP]]"
PROTECT_CLOSE = "[[/KEEP]]"


def est_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


def extract_protected(text: str) -> list:
    """Pull [[KEEP]]...[[/KEEP]] regions - protected zones that must never be trimmed."""
    return re.findall(
        re.escape(PROTECT_OPEN) + r"(.*?)" + re.escape(PROTECT_CLOSE), text, re.DOTALL
    )


def quality_gate(before: str, after: str, extra_protected: list = None) -> dict:
    """Ensure compression did not drop protected content. pass + missing list."""
    protected = extract_protected(before)
    if extra_protected:
        protected += extra_protected
    missing = [p.strip()[:80] for p in protected if p.strip() and p.strip() not in after]
    return {"pass": len(missing) == 0, "missing": missing, "checked": len(protected)}
