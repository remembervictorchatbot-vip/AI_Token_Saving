#!/usr/bin/env python3
"""Integration tests for the toks-mcp server (spawns it as a real subprocess)."""
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "toks_mcp_server.py")
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "..",
                                        "skills", "token-savings", "scripts"))


class McpProc:
    """Context manager: spawn server, newline JSON-RPC helpers."""

    def __init__(self):
        self.p = subprocess.Popen(
            [sys.executable, SERVER, "--scripts-dir", SCRIPTS],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)

    def send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def read(self):
        line = self.p.stdout.readline()
        return json.loads(line) if line.strip() else {}

    def rpc(self, method, params=None, rid=1):
        req = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            req["params"] = params
        self.send(req)
        return self.read()

    def close(self):
        try:
            self.p.terminate()
        except Exception:
            pass


class TestToksMcpServer(unittest.TestCase):
    def test_handshake_and_tools_list(self):
        m = McpProc()
        try:
            r = m.rpc("initialize", {"protocolVersion": "2025-06-18",
                                     "capabilities": {},
                                     "clientInfo": {"name": "t", "version": "1"}})
            self.assertEqual(r["result"]["protocolVersion"], "2025-06-18")
            self.assertEqual(r["result"]["serverInfo"]["name"], "toks")
            r = m.rpc("tools/list", rid=2)
            names = [t["name"] for t in r["result"]["tools"]]
            self.assertEqual(names, ["compress_context", "retrieve_original",
                                     "search_tools", "skills_search", "auto_sweep"])
        finally:
            m.close()

    def test_compress_and_retrieve_roundtrip(self):
        import time
        m = McpProc()
        try:
            m.rpc("initialize", {"protocolVersion": "2024-11-05"})
            # unique content so the shared dedup cache doesn't turn it into a §ref
            big = "unique ccr roundtrip {} — repeated block\n".format(time.time_ns()) + \
                  "repeated content line\n" * 200
            r = m.rpc("tools/call", {"name": "compress_context",
                                     "arguments": {"text": big}}, rid=3)
            text = r["result"]["content"][0]["text"]
            self.assertIn("ccr:", text)
            h = [ln for ln in text.splitlines() if ln.startswith("[ccr:")][0]
            h = h.strip("[]").replace("ccr:", "")
            r = m.rpc("tools/call", {"name": "retrieve_original",
                                     "arguments": {"hash": h}}, rid=4)
            back = r["result"]["content"][0]["text"]
            self.assertEqual(back, big, "CCR must return the verbatim original")
        finally:
            m.close()

    def test_unknown_tool_error(self):
        m = McpProc()
        try:
            m.rpc("initialize", {"protocolVersion": "2024-11-05"})
            r = m.rpc("tools/call", {"name": "nope"}, rid=5)
            self.assertEqual(r["error"]["code"], -32602)
        finally:
            m.close()

    def test_method_not_found(self):
        m = McpProc()
        try:
            m.rpc("initialize", {"protocolVersion": "2024-11-05"})
            r = m.rpc("resources/list", rid=6)
            self.assertEqual(r["error"]["code"], -32601)
        finally:
            m.close()

    def test_skills_search(self):
        m = McpProc()
        try:
            m.rpc("initialize", {"protocolVersion": "2024-11-05"})
            r = m.rpc("tools/call", {"name": "skills_search",
                                     "arguments": {"query": "compress tokens"}}, rid=7)
            self.assertIn("token-savings", r["result"]["content"][0]["text"])
        finally:
            m.close()

    def test_search_tools(self):
        m = McpProc()
        try:
            m.rpc("initialize", {"protocolVersion": "2024-11-05"})
            manifest = json.dumps({"connectors": [{"name": "gh", "tools": [
                {"name": "create_pr", "schema_chars": 500,
                 "desc": "create pull request"}]}]})
            r = m.rpc("tools/call", {"name": "search_tools",
                                     "arguments": {"manifest": manifest,
                                                   "query": "pull request"}}, rid=8)
            self.assertIn("gh.create_pr", r["result"]["content"][0]["text"])
        finally:
            m.close()

    def test_auto_sweep_smoke(self):
        m = McpProc()
        try:
            m.rpc("initialize", {"protocolVersion": "2024-11-05"})
            r = m.rpc("tools/call", {"name": "auto_sweep"}, rid=9)
            self.assertIn("full-auto sweep", r["result"]["content"][0]["text"])
        finally:
            m.close()


if __name__ == "__main__":
    unittest.main()
