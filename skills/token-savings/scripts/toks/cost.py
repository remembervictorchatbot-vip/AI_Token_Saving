"""Input-side cost preflight - "estimate before execute" (new, v8).

Provider-agnostic token/cost estimation. Token estimate = chars/4 (same rule
as bench). Prices are NOT hardcoded to any provider: pass your provider price
per 1M tokens via --price-per-mtok or TOKS_PRICE_PER_MT (default 1.0
currency unit). Peak/idle multipliers (2x / 0.5x) are the common tiered-pricing
shape; override with --peak / --idle.

Step-cost model (the reason this command exists):
    total = uncached_input + steps * cached_input_re-read + output
The cached re-read term dominates: every step re-sends the whole context from
prefix cache, so cost grows with STEPS * CONTEXT, not with what you wrote.
This is why hygiene (fresh threads every 8-10 turns) and batching matter more
than micro-compression. See SKILL.md Part G.
"""

from toks import measure


DEFAULT_PRICE_PER_MT = 1.0   # currency units per 1M tokens (set yours!)


def est_tokens(text: str) -> int:
    """Chars/4 - the same provider-agnostic estimate bench uses."""
    return measure.est_tokens(text)


def estimate(
    steps: int,
    ctx_chars: int,
    out_chars: int = 4000,
    price_per_mtok: float = DEFAULT_PRICE_PER_MT,
    peak: bool = True,
) -> dict:
    """Estimate session token spend. Returns a structured result."""
    steps = max(1, steps)
    uncached_in = max(1, ctx_chars // 4)
    cached_in = max(1, ctx_chars // 4) * steps
    output = max(1, out_chars // 4)
    total = uncached_in + cached_in + output
    mult = 2.0 if peak else 0.5
    return {
        "steps": steps,
        "ctx_chars": ctx_chars,
        "out_chars": out_chars,
        "uncached_in_tok": uncached_in,
        "cached_in_tok": cached_in,
        "output_tok": output,
        "total_tok": total,
        "peak": peak,
        "multiplier": mult,
        "price_per_mtok": price_per_mtok,
        "cost": round(total / 1e6 * price_per_mtok * mult, 4),
    }


def format_report(e: dict) -> str:
    """Human-readable estimate report."""
    mode = "PEAK (2x)" if e["peak"] else "IDLE (0.5x)"
    return (
        "cost-estimate: {steps} steps, ctx {ctx} chars, out {out} chars\n"
        "  uncached input : {unc:,} tok\n"
        "  cached re-read : {cached:,} tok  (steps x ctx - the dominant term)\n"
        "  output         : {out_tok:,} tok\n"
        "  TOTAL          : {total:,} tok\n"
        "  mode           : {mode} | price {price} /MT\n"
        "  est. cost      : {cost:.4f}".format(
            steps=e["steps"], ctx=e["ctx_chars"], out=e["out_chars"],
            unc=e["uncached_in_tok"], cached=e["cached_in_tok"],
            out_tok=e["output_tok"], total=e["total_tok"],
            mode=mode, price=e["price_per_mtok"], cost=e["cost"],
        )
    )