"""Tool-surface enhancement (v11d): Tool-Search index + defer_loading plan.

The Claude "Tool Search Tool" pattern (advanced-tool-use, 2025-11): instead of
injecting every tool's full JSON schema into every request, load upfront only
a tiny search index — one line per tool: name + one-sentence description
(~30 tokens) — plus a handful of always-on critical tools. Full schemas are
deferred (`defer_loading: true`) and materialized on demand when a query
matches.

This module builds that layer for ANY harness from the same manifest format
toolaudit uses:
  - `build_index`:   name+description lines, grouped by connector
  - `plan_defer`:    which tools to mark defer_loading:true vs keep upfront
                     (keep = explicit keep-list + top-frequency share)
  - `search_tools`:  regex/BM25-lite scoring over the index (stdlib tf-idf-ish)
  - `estimate`:      before/after tokens/call for the plan

Pure stdlib, deterministic. Recommend-only: emits a plan; applying it is the
harness owner's action.
"""
import math
import re

from toks.toolaudit import parse_manifest, _tokens_for

INDEX_LINE_BUDGET = 30          # est. tokens per index line (name + one-liner)
DEFAULT_UPFRONT_KEEP = 5        # always-on critical tools besides the searcher


def _one_liner(desc: str, maxlen: int = 80) -> str:
    d = re.sub(r"\s+", " ", str(desc or "")).strip()
    return d[:maxlen].rstrip() + ("…" if len(d) > maxlen else "")


def build_index(manifest) -> str:
    """One line per tool: `connector.tool — description`. This is ALL an agent
    needs to decide relevance; full schemas load on demand."""
    connectors = parse_manifest(manifest) if isinstance(manifest, (str, dict)) else manifest
    lines = []
    for c in connectors:
        for t in c["tools"]:
            desc = t.get("desc") or t.get("description") or ""
            lines.append("{}.{} — {}".format(c["name"], t["name"], _one_liner(desc)))
    return "\n".join(lines)


def plan_defer(manifest, keep=None, max_upfront=DEFAULT_UPFRONT_KEEP):
    """Return the defer_loading plan: upfront tools + deferred count +
    projected token cost before/after."""
    connectors = parse_manifest(manifest) if isinstance(manifest, (str, dict)) else manifest
    keep = list(keep or [])
    flat = [(c["name"], t) for c in connectors for t in c["tools"]]
    upfront = [n for n in keep]
    for cname, t in flat:
        if len(upfront) >= max_upfront:
            break
        if (cname + "." + t["name"]) not in upfront and t["name"] not in upfront:
            upfront.append(t["name"])
    upfront_set = set(upfront)
    deferred = [(cn, t) for cn, t in flat
                if t["name"] not in upfront_set and (cn + "." + t["name"]) not in upfront_set]
    before = _tokens_for([t for _, t in flat])
    after = len(flat) * 0  # placeholder replaced below
    after = (len(flat) * INDEX_LINE_BUDGET) + _tokens_for(
        [t for cn, t in flat if t["name"] in upfront_set or (cn + "." + t["name"]) in upfront_set])
    return {
        "total_tools": len(flat),
        "upfront": upfront,
        "deferred_count": len(deferred),
        "tokens_before": before,
        "tokens_after": round(after),
        "saved_pct": round(100.0 * (before - after) / before, 1) if before else 0.0,
    }


_WORD_RE = re.compile(r"[a-z0-9_]+")


def _terms(s: str):
    return set(_WORD_RE.findall(s.lower()))


def search_tools(manifest, query: str, top: int = 5):
    """Lite BM25-flavored scorer over name+description terms. Returns ranked
    `connector.tool` names — the harness then loads those schemas on demand."""
    connectors = parse_manifest(manifest) if isinstance(manifest, (str, dict)) else manifest
    q = _terms(query)
    if not q:
        return []
    docs = []
    for c in connectors:
        for t in c["tools"]:
            docs.append((c["name"] + "." + t["name"],
                         _terms(t["name"]) | _terms(t.get("desc") or "")))
    n_docs = len(docs) or 1
    idf = {}
    for term in q:
        df = sum(1 for _, d in docs if term in d)
        idf[term] = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
    scored = []
    for name, d in docs:
        score = sum(idf[term] for term in q if term in d)
        if score > 0:
            scored.append((round(score, 3), name))
    scored.sort(reverse=True)
    return [name for _, name in scored[:top]]


def estimate_report(plan: dict) -> str:
    return (
        "tool-search surface plan\n"
        "  total tools     : {t}\n"
        "  upfront (always): {u} {ulist}\n"
        "  deferred        : {d} (schemas load on search hit)\n"
        "  tokens/call     : {b:,} -> {a:,} ({s}% saved)".format(
            t=plan["total_tools"], u=len(plan["upfront"]),
            ulist=", ".join(plan["upfront"][:6]) + ("…" if len(plan["upfront"]) > 6 else ""),
            d=plan["deferred_count"], b=plan["tokens_before"],
            a=plan["tokens_after"], s=plan["saved_pct"]))
