"""Guarantee [[KEEP]]...[[/KEEP]] protected zones survive ANY compressor.

The unified skill promises "compressed never means lost". But aggressive
compressors can drop protected content incidentally - e.g. astrip strips
comment lines, and a [[KEEP]] zone placed in a comment would vanish; JSON
minification could mangle an embedded marker. This wrapper makes the promise
mechanical: extract protected zones, compress ONLY the remainder, then restore
the zones verbatim. No compressor can drop a user's literal ID/path/constraint.

Placeholders use a per-call UUID token (valid in source code, JSON, and prose,
and impossible to collide with real content) instead of NUL bytes - Python
source cannot contain NUL, so a NUL placeholder would force AST parsing to fail.
"""
import uuid

from toks import measure

PLACE_PREFIX = "@@KPROT_"
PLACE_SUFFIX = "_KPROT@@"


def compress_protected(text: str, compressor) -> str:
    """Run `compressor(safe_text) -> str` while guaranteeing protected zones survive.

    `compressor` may be any callable. Placeholder tokens are unique per call and
    entirely ASCII, so they survive source parsers, JSON serializers, and prose.
    """
    zones = measure.extract_protected(text)
    tokens = [f"{PLACE_PREFIX}{uuid.uuid4().hex}{i}{PLACE_SUFFIX}" for i in range(len(zones))]
    safe = text
    for tok, z in zip(tokens, zones):
        safe = safe.replace(f"{measure.PROTECT_OPEN}{z}{measure.PROTECT_CLOSE}", tok, 1)
    compressed = compressor(safe) if callable(compressor) else safe
    out = compressed
    for tok, z in zip(tokens, zones):
        out = out.replace(tok, f"{measure.PROTECT_OPEN}{z}{measure.PROTECT_CLOSE}")
    return out
