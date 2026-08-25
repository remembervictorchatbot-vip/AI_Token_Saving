"""Smart auto-compress policy (v11c).

Answers "should this content be compressed?" with a ratio threshold plus
quality guards, synthesizing the best current practice:

- LLMLingua: dynamic per-segment ratios; only keep compression that meets a
  minimum saving target.
- Claude Code / compaction research: compress EARLY and predictably, never so
  late that quality degrades; typed markers only when they earn their cost.
- LeanCTX adaptive depth + shadow gating: measure what compression WOULD do,
  back off when it hurts (cache-busting, tiny wins, protected-heavy content),
  and offer a SHADOW verdict (report-only) before enforcing.

Policy (decide):
  SKIP   - too short, unsafe content, or projected savings < min_ratio
  SHADOW - between min_ratio and enforce_ratio: report what would happen
           without changing anything (default min 0.3, enforce 0.5)
  APPLY  - projected savings >= enforce_ratio AND quality guard passes

Quality guard (would hurt -> downgrade APPLY to SHADOW):
  - protected ([[KEEP]]) zones dominate (>60% of content)
  - content is code where astrip would drop >90% of lines (likely needed bodies)
Pure stdlib, deterministic.
"""
from toks import compress, measure, safemode

DEFAULT_MIN_RATIO = 0.3     # user spec: 30%+ savings => auto
DEFAULT_ENFORCE_RATIO = 0.5


def _project(text: str) -> tuple:
    """Best-effort projection: returns (compressed_text, saved_ratio)."""
    stripped = text.lstrip()
    if stripped[:1] in "[{":
        try:
            import json
            out = compress.compress_json(json.loads(text))
        except Exception:
            out = compress.trim_bash(text)
    elif "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
        from toks import mdnorm
        try:
            out = mdnorm.html_to_markdown(text)
        except Exception:
            out = compress.trim_bash(text)
    else:
        out = compress.trim_bash(text)
    if len(out) >= len(text):
        return text, 0.0
    return out, round(1.0 - len(out) / len(text), 3)


def decide(text: str, min_ratio: float = DEFAULT_MIN_RATIO,
           enforce_ratio: float = DEFAULT_ENFORCE_RATIO) -> dict:
    """Smart auto-compress decision for a piece of context."""
    if not text or len(text) < 200:
        return {"verdict": "SKIP", "why": "too short (<200 chars)",
                "saved_ratio": 0.0, "out": text}
    if safemode.risk_level(text) == "unsafe":
        return {"verdict": "SKIP", "why": "safemode: verbatim required",
                "saved_ratio": 0.0, "out": text}
    out, ratio = _project(text)
    kept = len(measure.extract_protected(text))
    protected_heavy = bool(text) and kept / max(1, len(text)) > 0.6
    if ratio < min_ratio:
        return {"verdict": "SKIP",
                "why": "projected {:.0%} < min {:.0%}".format(ratio, min_ratio),
                "saved_ratio": ratio, "out": text}
    guarded = protected_heavy
    if ratio >= enforce_ratio and not guarded:
        return {"verdict": "APPLY", "why": "{:.0%} >= enforce {:.0%}".format(
                    ratio, enforce_ratio),
                "saved_ratio": ratio, "out": out}
    return {"verdict": "SHADOW",
            "why": ("{:.0%} in [{:.0%},{:.0%}) band".format(ratio, min_ratio, enforce_ratio)
                    if not guarded else
                    "quality guard: {:.0%} protected content".format(kept / max(1, len(text)))),
            "saved_ratio": ratio, "out": out}


def format_report(res: dict) -> str:
    line = "auto-compress: {} ({})".format(res["verdict"], res["why"])
    if res["verdict"] == "APPLY":
        line += "\n{} chars -> {} chars".format(
            len(res.get("out", "")) + 0, len(res["out"]))
    return line
