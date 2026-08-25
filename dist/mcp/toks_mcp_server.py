#!/usr/bin/env python3
"""toks-mcp: MCP stdio server exposing the toks toolkit (v15).

Lazy-loading meta-tool pattern: 5 schemas (~250 tok) give any MCP host the
whole discipline. Wraps gate/ccr/toolsearch/skills_mgmt/full_auto — no new
logic, adapters only.

Protocol: JSON-RPC 2.0 over stdio, newline-delimited. Negotiates the client's
protocolVersion (fallback 2024-11-05). Diagnostics go to stderr; stdout is
JSON-RPC only.

Run:    python3 toks_mcp_server.py [--scripts-dir PATH] [--allow-root PATH]
Test:   python3 test_server.py
"""
import json
import os
import sys

PROTOCOL_FALLBACK = "2024-11-05"
SERVER_INFO = {"name": "toks", "version": "15.0.0"}

DEFAULT_SCRIPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "skills", "token-savings", "scripts"))

TOOLS = [
    {
        "name": "compress_context",
        "description": ("Compress text before it enters LLM context: tiered "
                        "compression (JSON/HTML/log/prose), dedup refs, "
                        "protected [[KEEP]] zones, secrets pass verbatim. "
                        "Reversible — returns a [ccr:<hash>] marker; recover "
                        "the verbatim original with retrieve_original."),
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "content to compress"}},
            "required": ["text"],
        },
    },
    {
        "name": "retrieve_original",
        "description": ("Return the verbatim original for a [ccr:<hash>] marker "
                        "from compress_context. Miss if expired (>30d) or unknown."),
        "inputSchema": {
            "type": "object",
            "properties": {"hash": {"type": "string", "description": "ccr hash"}},
            "required": ["hash"],
        },
    },
    {
        "name": "search_tools",
        "description": ("Search a tool manifest ({'connectors': [...]}) by query; "
                        "returns ranked tool names + a one-line discovery index "
                        "(Claude Tool-Search pattern)."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "manifest": {"type": "string", "description": "JSON manifest"},
                "query": {"type": "string"},
            },
            "required": ["manifest"],
        },
    },
    {
        "name": "skills_search",
        "description": ("Search installed skills' name+description index without "
                        "loading bodies. Returns matching skill names."),
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "auto_sweep",
        "description": ("One-call health report: wiring check, live tool surfaces "
                        "(estimates in this mode), skills audit, prioritized fixes."),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


class ToksMcpServer:
    """Dispatch table server. Import of toks modules is lazy per-call so a
    broken import degrades one tool, not the whole server."""

    def __init__(self, scripts_dir=None):
        self.scripts_dir = scripts_dir or DEFAULT_SCRIPTS_DIR
        if self.scripts_dir not in sys.path:
            sys.path.insert(0, self.scripts_dir)

    # --- tool impls -------------------------------------------------------
    def t_compress_context(self, args):
        from toks import gate
        return gate.gate_content(args.get("text", ""))

    def t_retrieve_original(self, args):
        from toks import ccr
        res = ccr.CCR().retrieve(args.get("hash", ""))
        if res["hit"]:
            return res["text"]
        return "[ccr MISS] {}".format(res.get("why", "unknown"))

    def t_search_tools(self, args):
        from toks import toolsearch
        raw = args.get("manifest", "")
        out = []
        if args.get("query"):
            out.append("matches: " + ", ".join(
                toolsearch.search_tools(raw, args["query"])) or "no matches")
        out.append(toolsearch.build_index(raw))
        return "\n".join(out)

    def t_skills_search(self, args):
        from toks import skills_mgmt
        root = os.path.expanduser("~/.hermes/skills")
        if not os.path.isdir(root):
            return "no skills dir found"
        skills = skills_mgmt.scan_skills(root)
        hits = skills_mgmt.search_index(skills, args.get("query", ""), top=8)
        return "\n".join(hits) if hits else "no matches"

    def t_auto_sweep(self, args):
        from toks import full_auto
        res = full_auto.auto()
        rep = full_auto.format_report(res)
        # strip live-handshake cost: auto() runs live; keep it but cap output
        return rep[:4000]

    # --- dispatch ---------------------------------------------------------
    def call_tool(self, name, args):
        mapping = {
            "compress_context": self.t_compress_context,
            "retrieve_original": self.t_retrieve_original,
            "search_tools": self.t_search_tools,
            "skills_search": self.t_skills_search,
            "auto_sweep": self.t_auto_sweep,
        }
        fn = mapping.get(name)
        if not fn:
            raise KeyError("unknown tool: {}".format(name))
        result = fn(args or {})
        return str(result) if result is not None else ""

    def handle(self, req: dict) -> dict:
        method = req.get("method", "")
        rid = req.get("id")
        is_notification = rid is None

        def reply(result):
            return {"jsonrpc": "2.0", "id": rid, "result": result}

        def error(code, message):
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": code, "message": message}}

        if method == "initialize":
            client_ver = (req.get("params") or {}).get("protocolVersion",
                                                       PROTOCOL_FALLBACK)
            return reply({
                "protocolVersion": client_ver,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            })
        if method == "notifications/initialized":
            return None if is_notification else reply({})
        if method == "tools/list":
            return reply({"tools": TOOLS})
        if method == "tools/call":
            params = req.get("params") or {}
            try:
                text = self.call_tool(params.get("name", ""),
                                      params.get("args") or params.get("arguments") or {})
                if is_notification:
                    return None
                return reply({"content": [{"type": "text", "text": text}]})
            except KeyError as e:
                return error(-32602, str(e))
            except Exception as e:
                return error(-32603, "tool failed: {}: {}".format(
                    type(e).__name__, e))
        if is_notification:
            return None
        return error(-32601, "method not found: {}".format(method))


def serve(scripts_dir=None):
    srv = ToksMcpServer(scripts_dir)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700,
                                        "message": "parse error"}}), flush=True)
            continue
        resp = srv.handle(req)
        if resp is not None:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    scripts = None
    if "--scripts-dir" in sys.argv:
        scripts = sys.argv[sys.argv.index("--scripts-dir") + 1]
    serve(scripts)
