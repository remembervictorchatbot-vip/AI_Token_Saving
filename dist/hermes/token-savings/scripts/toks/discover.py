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
    out = []
    for n, cfg in servers.items():
        cmd = None
        if isinstance(cfg, dict) and cfg.get("command"):
            cmd = [cfg["command"]] + list(cfg.get("args") or [])[:4]
        out.append({"name": n, "_cmd": cmd})
    return out


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
    block = text[m.end():]
    names = re.findall(r"^  ([\w-]+):\s*$", block, re.M)
    out = []
    for n in names[:10]:
        # best-effort command extraction: `command: <v>` within next lines at
        # 4-space indent under this server key
        sm = re.search(r"^  {}:\n((?:    .*\n?)+)".format(re.escape(n)), block, re.M)
        cmd = None
        if sm:
            cm = re.search(r"^\s+command:\s*(\S+)", sm.group(1), re.M)
            args = re.findall(r"^\s+-\s+(\S+)", sm.group(1), re.M)
            if cm:
                cmd = [cm.group(1)] + args[:4]
        out.append({"name": n, "_cmd": cmd})
    return out


def discover(live: bool = False, timeout: int = 20) -> dict:
    """Build the tool manifest. live=True performs real MCP handshakes
    (initialize -> tools/list) for servers whose command is known; failures
    fall back to estimates and are reported."""
    seen, conns, command_map = set(), [], {}
    for c in _from_claude_code() + _from_hermes():
        name = c["name"]
        if name in seen:
            continue
        seen.add(name)
        cmd = c.get("_cmd")
        if cmd:
            command_map[name] = cmd
        conns.append({"name": name,
                      "tool_count": EST_TOOLS_DEFAULT,
                      "avg_schema_chars": EST_SCHEMA_CHARS})
    manifest = {"connectors": conns,
                "_note": "tool_count/schema_chars are estimates; "
                         "replace with live handshake counts when available"}
    if live:
        from toks import mcp_client
        manifest = mcp_client.enrich_manifest(manifest, command_map,
                                              timeout=timeout)
    return manifest


def format_report(m: dict) -> str:
    live = m.get("live")
    lines = ["discovered connectors: {}".format(len(m["connectors"]))]
    for c in m["connectors"]:
        if "tools" in c:
            est = (sum(t["schema_chars"] for t in c["tools"]) + 3) // 4
            detail = "LIVE {} tools".format(len(c["tools"]))
        else:
            est = (c["tool_count"] * c["avg_schema_chars"] + 3) // 4
            detail = "estimate"
        lines.append("  - {} (~{:,} tok/call, {})".format(c["name"], est, detail))
    if live is not None:
        lines.append("  live handshake: {} | estimated: {}".format(
            len(live or []), len(m["connectors"]) - len(live or [])))
    lines.append("next: toks toolaudit --manifest | toks tool-search --manifest")
    return "\n".join(lines)
