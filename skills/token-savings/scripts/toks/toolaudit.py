"""Connector tool-surface audit (USE-7) - recommend-only, NEVER disconnects.

Every connected MCP/tool server injects its schema into every request. A rich
surface can cost tens of thousands of tokens per call whether or not the tools
are used this turn. This module AUDITS that cost and RECOMMENDS what to keep vs
review. It does NOT disconnect anything - that is a user action, and the skill
documents how, but the tool never performs it.

Input is a manifest (dict or JSON string):

    {"connectors": [
        {"name": "kdocs", "tools": [
            {"name": "wpp.create_presentation", "schema_chars": 1200},
            ...
        ]},
        {"name": "feishu", "tool_count": 80, "avg_schema_chars": 900},  # flat form
        ...
    ]}

Token estimate is provider-agnostic: chars/4 (matches the toolkit's fallback
ratio), so the tool has zero external dependencies.
"""
import json

DEFAULT_THRESHOLD_PCT = 20.0      # a connector above this share is a review candidate
DEFAULT_ABS_FLOOR = 5000          # or above this many estimated tokens/call


def parse_manifest(text_or_obj):
    """Accept a JSON string or a dict; return the normalized connector list."""
    obj = json.loads(text_or_obj) if isinstance(text_or_obj, str) else text_or_obj
    if not isinstance(obj, dict) or "connectors" not in obj:
        raise ValueError("manifest must be {'connectors': [...]} (or a list)")
    items = obj["connectors"]
    out = []
    for c in items:
        name = c.get("name") or c.get("id") or "unknown"
        if "tools" in c and isinstance(c["tools"], list):
            tools = [
                {"name": t.get("name", "tool"), "schema_chars": int(t.get("schema_chars", 1500))}
                for t in c["tools"]
            ]
        else:
            n = int(c.get("tool_count", 0))
            avg = int(c.get("avg_schema_chars", 1500))
            tools = [{"name": f"{name}#{i}", "schema_chars": avg} for i in range(n)]
        out.append({"name": name, "tools": tools})
    return out


def _tokens_for(tools):
    return sum((t["schema_chars"] + 3) // 4 for t in tools)


def audit_connectors(manifest, threshold_pct=DEFAULT_THRESHOLD_PCT,
                     abs_token_floor=DEFAULT_ABS_FLOOR, keep=None):
    """Audit connector tool-surface cost. Returns a structured report dict.

    Never mutates state, never disconnects - pure analysis + recommendation.
    """
    connectors = parse_manifest(manifest)
    keep = set(keep or [])

    rows = []
    for c in connectors:
        toks = _tokens_for(c["tools"])
        rows.append({
            "name": c["name"],
            "tool_count": len(c["tools"]),
            "est_tokens_per_call": toks,
            "pct": 0.0,  # filled after total known
        })
    total = sum(r["est_tokens_per_call"] for r in rows) or 1
    for r in rows:
        r["pct"] = round(100.0 * r["est_tokens_per_call"] / total, 1)

    # Rank by cost, highest first.
    rows.sort(key=lambda r: r["est_tokens_per_call"], reverse=True)

    for r in rows:
        is_keep = r["name"] in keep
        is_candidate = (
            (r["pct"] >= threshold_pct or r["est_tokens_per_call"] >= abs_token_floor)
            and not is_keep
        )
        r["recommendation"] = "keep (explicit)" if is_keep else (
            "review (prune candidate)" if is_candidate else "keep"
        )
        r["auto_disconnected"] = False   # explicit guarantee: this tool never disconnects

    review = [r["name"] for r in rows if r["recommendation"].startswith("review")]
    return {
        "total_est_tokens_per_call": total,
        "connector_count": len(rows),
        "review_candidates": review,
        "disconnected_any": False,        # hard guarantee for the SOP/USE-7 rule
        "rows": rows,
        "params": {
            "threshold_pct": threshold_pct,
            "abs_token_floor": abs_token_floor,
            "kept_explicit": sorted(keep),
        },
    }


def format_report(result: dict) -> str:
    """Render the audit as a short Markdown report."""
    lines = []
    lines.append("# Tool-surface audit (recommend-only)")
    lines.append("")
    lines.append(
        f"Connected surfaces: **{result['connector_count']}** | "
        f"estimated cost: **~{result['total_est_tokens_per_call']:,} tokens/call**"
    )
    lines.append("")
    lines.append("| Connector | Tools | Tokens/call | Share | Recommendation |")
    lines.append("|-----------|-------|-------------|-------|----------------|")
    for r in result["rows"]:
        lines.append(
            f"| {r['name']} | {r['tool_count']} | {r['est_tokens_per_call']:,} "
            f"| {r['pct']}% | {r['recommendation']} |"
        )
    lines.append("")
    if result["review_candidates"]:
        lines.append("**Review candidates (prune to save tokens):** "
                     + ", ".join(result["review_candidates"]))
    else:
        lines.append("No prune candidates at current thresholds.")
    lines.append("")
    lines.append(
        "> Action is a USER decision. This tool AUDITS and RECOMMENDS only - "
        "it never disconnects a connector. To act, review connected connectors "
        "and disable the unused ones in the host settings."
    )
    return "\n".join(lines)


def sample_manifest() -> str:
    """Return a small example manifest JSON string for demos and testing."""
    return json.dumps({
        "connectors": [
            {"name": "kdocs", "tools": [
                {"name": "wpp.create_presentation", "schema_chars": 1800},
                {"name": "wpp.read_presentation", "schema_chars": 1500},
                {"name": "sheet.create", "schema_chars": 1600},
            ]},
            {"name": "feishu", "tool_count": 60, "avg_schema_chars": 1200},
            {"name": "notion", "tool_count": 12, "avg_schema_chars": 900},
            {"name": "agent-mail", "tool_count": 8, "avg_schema_chars": 700},
        ]
    })
