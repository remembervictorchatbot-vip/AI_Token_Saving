"""Live tool-surface discovery (v12 prototype).

Auto-builds a toks manifest from real harness configs — no manual manifest
writing. Sources (best-effort, skip missing):
  - Claude Code: ~/.claude.json mcpServers
  - Hermes:      ~/.hermes/config.yaml mcp_servers
  - OpenCode:    ~/.config/opencode/opencode.jsonc mcp

Tool counts are estimates until a live MCP handshake is performed; run
`toks toolaudit` / `toks tool-search` on the output. Recommend-only.
"""
import json
import os
import re

EST_TOOLS_DEFAULT = 10
EST_SCHEMA_CHARS = 900


def _from_claude_code():
    p = os.path.expanduser("~/.claude.json")
    if not os.path.exists(p):
        return []
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    servers = {}

    def find(o, depth=0):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "mcpServers" and isinstance(v, dict):
                    servers.update(v)
                elif isinstance(v, (dict, list)) and depth < 4:
                    find(v, depth + 1)
    find(d)
    return [{"name": n} for n in servers]


def _from_hermes():
    p = os.path.expanduser("~/.hermes/config.yaml")
    if not os.path.exists(p):
        return []
    try:
        text = open(p, encoding="utf-8").read()
    except Exception:
        return []
    m = re.search(r"^mcp_servers:\s*$", text, re.M)
    if not m:
        return []
    names = re.findall(r"^  ([\w-]+):\s*$", text[m.end():], re.M)
    return [{"name": n} for n in names[:10]]


def discover() -> dict:
    seen, conns = set(), []
    for c in _from_claude_code() + _from_hermes():
        if c["name"] not in seen:
            seen.add(c["name"])
            conns.append({"name": c["name"],
                          "tool_count": EST_TOOLS_DEFAULT,
                          "avg_schema_chars": EST_SCHEMA_CHARS})
    return {"connectors": conns,
            "_note": "tool_count/schema_chars are estimates; "
                     "replace with live handshake counts when available"}


def format_report(m: dict) -> str:
    lines = ["discovered connectors: {}".format(len(m["connectors"]))]
    for c in m["connectors"]:
        est = (c["tool_count"] * c["avg_schema_chars"] + 3) // 4
        lines.append("  - {} (~{:,} tok/call est)".format(c["name"], est))
    lines.append("next: toks toolaudit --manifest | toks tool-search --manifest")
    return "\n".join(lines)
