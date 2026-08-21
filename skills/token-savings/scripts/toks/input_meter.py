"""Session-level input meter (v9): actual vs recoverable input cost.

Honest scope: without the ORIGINAL uncompressed content a true baseline is
unreconstructable. The meter reports what a transcript actually cost
(chars/4, same rule as bench) and quantifies the repeat content that dedup
would have collapsed - the dominant recoverable input waste.
"""
from toks import audit


def meter(text: str) -> dict:
    """Estimate actual input tokens and recoverable repeat waste."""
    blocks = audit._blocks(text)
    actual_chars = sum(len(b) for b in blocks)
    seen, dup_chars = set(), 0
    for b in blocks:
        if len(b) > 200:
            if b in seen:
                dup_chars += len(b)
            else:
                seen.add(b)
    return {
        "messages": len(blocks),
        "actual_chars": actual_chars,
        "actual_tok": actual_chars // 4,
        "repeat_chars": dup_chars,
        "repeat_tok": dup_chars // 4,
        "recoverable_pct": round(100.0 * dup_chars / actual_chars, 1) if actual_chars else 0.0,
    }


def format_report(m: dict) -> str:
    """Human-readable meter report."""
    return (
        "input-meter: {msgs} blocks | est input tokens {tok:,} ({chars:,} chars)\n"
        "  repeat content (dedup would collapse): {rtok:,} tok ({rp}%)".format(
            msgs=m["messages"], tok=m["actual_tok"], chars=m["actual_chars"],
            rtok=m["repeat_tok"], rp=m["recoverable_pct"])
    )