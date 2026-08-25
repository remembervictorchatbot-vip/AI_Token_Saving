"""One-command full-auto sweep (v13): `toks auto`.

The user-facing promise — "install the skill, everything is managed
automatically" — made literal. One invocation runs the whole discipline:

  1. doctor          — wiring check (python/toolkit/filter/PATH)
  2. discover --live — exact MCP tool surfaces (handshake, estimate fallback)
  3. toolaudit       — tool surface cost + prune candidates
  4. skills-audit    — near-dups / vague triggers / oversized / stale
  5. directives      — prioritized NEXT-ACTIONS the agent applies

Everything is recommend-only: `auto` reports and plans; destructive actions
(archiving, disconnecting) stay with the owner unless they invoke the named
follow-up commands themselves.

Pure stdlib, deterministic; degrades gracefully per section.
"""
from toks import doctor, skills_mgmt


def auto(skills_dir: str = "") -> dict:
    res = {"doctor": [], "tools": None, "skills": None, "issues": []}

    # 1. wiring
    res["doctor"] = doctor.run_checks()

    # 2+3. live tool surfaces + audit
    try:
        from toks import discover, toolaudit
        manifest = discover.discover(live=True, timeout=15)
        live = len(manifest.get("live", []))
        est = len(manifest.get("estimated", []))
        raw = _manifest_to_json(manifest["connectors"])
        audit_res = toolaudit.audit_connectors(raw) if raw else None
        res["tools"] = {"connectors": len(manifest["connectors"]),
                        "live": live, "estimated": est,
                        "audit": audit_res}
    except Exception as e:
        res["tools"] = {"error": str(e)[:80]}

    # 4. skills audit
    try:
        root = skills_dir or os_skills_root()
        if root and os.path.isdir(root):
            skills = skills_mgmt.scan_skills(root)
            res["skills"] = {"count": len(skills),
                             "index_tok": len(skills_mgmt.build_index(skills)) // 4,
                             "total_tok": sum(s["tok_est"] for s in skills)}
            res["issues"] = skills_mgmt.find_issues(skills)
    except Exception as e:
        res["skills"] = {"error": str(e)[:80]}

    return res


def os_skills_root() -> str:
    return os.path.expanduser("~/.hermes/skills")


import os  # noqa: E402  (used above)


def _manifest_to_json(connectors):
    """Serialize connectors into the JSON string toolaudit expects."""
    import json
    return json.dumps({"connectors": connectors})


def format_report(res: dict) -> str:
    lines = ["[toks auto] full-auto sweep", ""]

    # wiring
    ok = sum(1 for c in res["doctor"] if c["status"] == "ok")
    lines.append("wiring: {}/{} OK".format(ok, len(res["doctor"])))
    for c in res["doctor"]:
        if c["status"] != "ok" and c.get("fix"):
            lines.append("  fix {}: {}".format(c["check"], c["fix"]))
    lines.append("")

    # tools
    t = res.get("tools") or {}
    if "error" in t:
        lines.append("tools   : unavailable ({})".format(t["error"]))
    else:
        a = t.get("audit")
        total = a["total_est_tokens_per_call"] if a else 0
        lines.append("tools   : {} connectors ({} live handshake, {} estimated)"
                     .format(t.get("connectors", 0), t.get("live", 0), t.get("estimated", 0)))
        lines.append("  surface cost: ~{:,} tok/call{}".format(
            total, " | review: " + ", ".join(a["review_candidates"][:4])
            if a and a.get("review_candidates") else ""))
    lines.append("")

    # skills
    s = res.get("skills") or {}
    if "error" in s:
        lines.append("skills  : unavailable ({})".format(s["error"]))
    else:
        lines.append("skills  : {} installed | index ~{}, tok | bodies ~{:,} tok".format(
            s.get("count", 0), s.get("index_tok", 0), s.get("total_tok", 0)))
    by_type = {}
    for i in res["issues"]:
        by_type.setdefault(i["type"], []).append(i["skill"])
    for typ in ("DUPLICATE", "NEAR-DUP", "OVERSIZED", "STALE", "VAGUE-TRIGGER"):
        g = by_type.get(typ)
        if g:
            lines.append("  [{}] {}".format(typ, ", ".join(g[:4]) + ("…" if len(g) > 4 else "")))
    if not by_type:
        lines.append("  clean - no dupes/oversized/stale issues")
    lines.append("")

    # directives
    lines.append("[directives] apply in order:")
    n = 1
    for c in res["doctor"]:
        if c["status"] != "ok" and c.get("fix"):
            lines.append("  {}. wire: {}".format(n, c["fix"]))
            n += 1
    a = (res.get("tools") or {}).get("audit")
    if a and a.get("review_candidates"):
        lines.append("  {}. prune tool surfaces: {} (toks toolaudit)".format(
            n, ", ".join(a["review_candidates"][:3])))
        n += 1
    for typ in ("DUPLICATE", "NEAR-DUP"):
        g = by_type.get(typ)
        if g:
            lines.append("  {}. merge/archive duplicate skills: {} (keep one canonical)".format(n, ", ".join(g[:3])))
            n += 1
            break
    g = by_type.get("OVERSIZED")
    if g:
        lines.append("  {}. slim oversized SKILL.mds to references/detail.md: {}".format(
            n, ", ".join(g[:3])))
        n += 1
    if n == 1:
        lines.append("  1. nothing - all surfaces clean; re-run weekly")
    return "\n".join(lines)
