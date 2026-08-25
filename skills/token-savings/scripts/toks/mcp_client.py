"""Live MCP handshake (v12): exact tool surfaces, no estimates.

Speaks the MCP stdio protocol directly (JSON-RPC over stdin/stdout):
  initialize -> notifications/initialized -> tools/list -> terminate

For each connector discovered from harness configs this yields the REAL tool
list: name, description, inputSchema char count — replacing the estimates in
`discover`. Servers that fail to answer are reported unreachable (estimate
fallback), never crash the run.

Pure stdlib: subprocess + json. Recommend-only; read-only handshake.
"""
import json
import os
import subprocess

HANDSHAKE_TIMEOUT = 20   # seconds per server (connect + tools/list)


def _rpc(proc, obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def list_tools(command: str, args=None, env=None,
               timeout: int = HANDSHAKE_TIMEOUT) -> dict:
    """Run a full MCP handshake against one stdio server.
    Returns {"ok": bool, "tools": [...], "error": str?} where each tool is
    {"name", "desc", "schema_chars"}."""
    argv = [command] + list(args or [])
    try:
        proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True,
            env={**os.environ, **(env or {})})
    except OSError as e:
        return {"ok": False, "tools": [], "error": "spawn failed: {}".format(e)}

    def finish(result):
        try:
            proc.terminate()
        except Exception:
            pass
        return result

    try:
        _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05",
                               "capabilities": {},
                               "clientInfo": {"name": "toks", "version": "1.0"}}})
        init = json.loads(proc.stdout.readline() or "{}")  # type: ignore[union-attr]
        if "error" in init:
            return finish({"ok": False, "tools": [],
                           "error": init["error"].get("message", "init error")})
        _rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        line = proc.stdout.readline()
        if not line.strip():
            return finish({"ok": False, "tools": [],
                           "error": "empty tools/list response"})
        resp = json.loads(line)
        if "error" in resp:
            return finish({"ok": False, "tools": [],
                           "error": resp["error"].get("message", "tools/list error")})
        tools = []
        for t in resp.get("result", {}).get("tools", []):
            tools.append({
                "name": t.get("name", "tool"),
                "desc": (t.get("description") or "")[:120],
                "schema_chars": len(json.dumps(t.get("inputSchema", {}))),
            })
        return finish({"ok": True, "tools": tools})
    except Exception as e:  # timeout / JSON decode / broken pipe
        return finish({"ok": False, "tools": [],
                       "error": "{}: {}".format(type(e).__name__, e)})


def enrich_manifest(manifest: dict, command_map: dict,
                    timeout: int = HANDSHAKE_TIMEOUT) -> dict:
    """Replace estimated connectors with live data where a command is known.
    `command_map`: connector name -> [command, args...]. Unreachable servers
    keep their estimates; result reports which were live vs estimated."""
    out = {"connectors": [], "live": [], "estimated": []}
    for c in manifest.get("connectors", []):
        name = c["name"]
        cmd = command_map.get(name)
        if cmd:
            r = list_tools(cmd[0], cmd[1:], timeout=timeout)
            if r["ok"] and r["tools"]:
                out["connectors"].append({"name": name, "tools": r["tools"]})
                out["live"].append(name)
                continue
        out["connectors"].append(c)
        out["estimated"].append(name)
    return out


def format_report(res: dict) -> str:
    lines = ["live MCP surfaces"]
    for name in res.get("live", []):
        lines.append("  [LIVE ] {}".format(name))
    for name in res.get("estimated", []):
        lines.append("  [EST  ] {} (handshake failed or no command)".format(name))
    return "\n".join(lines)
