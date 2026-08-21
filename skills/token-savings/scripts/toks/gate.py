"""Automatic input gate (v9): context-ready content in one deterministic pass.

The mechanical form of the input discipline: any content crossing into context
passes the gate once. Pipeline: idempotency check -> safemode -> dedup (optional)
-> surface compression -> protected-zone protection -> marker report.

Quality guarantees (save tokens WITHOUT losing quality):
  - safemode : secrets / stack traces pass VERBATIM (0% compression)
  - protected: [[KEEP]]...[[/KEEP]] zones always survive (compress_protected)
  - idempotent: gated output is marked; re-gating is a no-op (no double loss)
  - never grows: if compression would enlarge the content, the original is kept
"""
import json

from toks import compress, dedup, mdnorm, measure, protect, safemode


GATE_MARK = "[toks-gate v1 saved={saved}% tiers={tiers} keep={keep} safemode={verdict}]"
MIN_COMPRESS = 80


def is_gated(text: str) -> bool:
    """True when the content was already passed through the gate (idempotency)."""
    return bool(text) and text.startswith("[toks-gate")


def _pick_compressor(text: str):
    """Choose the compression tier by content surface (json/html/log/prose)."""
    stripped = text.lstrip()
    if stripped[:1] in "[{":
        def as_json(t):
            try:
                return compress.compress_json(json.loads(t))
            except Exception:
                return compress.trim_bash(t, max_lines=200, collapse_repeats=3)
        return as_json
    if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
        def as_html(t):
            try:
                return mdnorm.html_to_markdown(t)
            except Exception:
                return compress.trim_bash(t, max_lines=200, collapse_repeats=3)
        return as_html
    return lambda t: compress.trim_bash(t, max_lines=200, collapse_repeats=3)


def _tier(text: str) -> str:
    """Surface tier name for the marker report."""
    stripped = text.lstrip()
    if stripped[:1] in "[{":
        return "json"
    if "<html" in text[:500].lower():
        return "html"
    if "\x1b[" in text:
        return "log"
    return "prose"


def gate_content(text: str, use_dedup: bool = True, min_compress: int = MIN_COMPRESS,
                 mark: bool = True) -> str:
    """Return context-ready content, or the original unchanged when the gate
    decides nothing should be compressed (short, already gated, or unsafe)."""
    if not text or len(text) < min_compress:
        return text
    if is_gated(text):
        return text
    if safemode.risk_level(text) == "unsafe":
        return text
    if use_dedup:
        r = dedup.DedupCache().ref(text)
        if r:
            return r
    keep = len(measure.extract_protected(text))
    out = protect.compress_protected(text, _pick_compressor(text))
    if len(out) >= len(text):
        return text
    if not mark:
        return out
    saved = round(100.0 * (len(text) - len(out)) / len(text))
    final = (GATE_MARK.format(saved=saved, tiers=_tier(text), keep=keep,
                              verdict=safemode.risk_level(text)) + "\n" + out)
    if len(final) >= len(text):
        return text   # marker would cost more than the compression saves
    return final