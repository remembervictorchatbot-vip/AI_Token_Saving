"""Tests for v12 mcp_client (live MCP handshake)."""
import sys
import tempfile
import unittest

from toks import mcp_client


class MockMCPServer:
    """Tiny stdio JSON-RPC MCP server for tests (runs in-process via a script)."""

    SCRIPT = r'''
import json, sys
for line in sys.stdin:
    try:
        req = json.loads(line)
    except Exception:
        continue
    if req.get("method") == "initialize":
        print(json.dumps({"jsonrpc": "2.0", "id": req["id"],
                          "result": {"protocolVersion": "2024-11-05",
                                     "capabilities": {"tools": {}},
                                     "serverInfo": {"name": "mock", "version": "0"}}}), flush=True)
    elif req.get("method") == "tools/list":
        tools = [{"name": "tool_a", "description": "Does alpha things",
                  "inputSchema": {"type": "object", "properties": {"x": {"type": "string"}}}},
                 {"name": "tool_b", "description": "Does beta things",
                  "inputSchema": {"type": "object"}}]
        print(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": {"tools": tools}}), flush=True)
'''


def _script_path():
    fh = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    fh.write(MockMCPServer.SCRIPT)
    fh.close()
    return fh.name


class TestMcpClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = _script_path()

    def test_list_tools_live(self):
        r = mcp_client.list_tools(sys.executable, [self.script], timeout=15)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([t["name"] for t in r["tools"]], ["tool_a", "tool_b"])
        self.assertGreater(r["tools"][0]["schema_chars"], 10)
        self.assertTrue(r["tools"][0]["desc"].startswith("Does alpha"))

    def test_spawn_failure_reported(self):
        r = mcp_client.list_tools("/nonexistent/binary-xyz", timeout=5)
        self.assertFalse(r["ok"])
        self.assertIn("spawn failed", r["error"])

    def test_enrich_manifest_replaces_live(self):
        manifest = {"connectors": [
            {"name": "mock", "tool_count": 10, "avg_schema_chars": 900}]}
        res = mcp_client.enrich_manifest(manifest, {"mock": [sys.executable, self.script]})
        self.assertIn("mock", res["live"])
        conn = next(c for c in res["connectors"] if c["name"] == "mock")
        self.assertEqual(len(conn["tools"]), 2)

    def test_enrich_manifest_falls_back_to_estimate(self):
        manifest = {"connectors": [
            {"name": "dead", "tool_count": 3, "avg_schema_chars": 100}]}
        res = mcp_client.enrich_manifest(manifest, {})
        self.assertIn("dead", res["estimated"])

    def test_format_report(self):
        self.assertIn("[LIVE ]", mcp_client.format_report({"live": ["a"], "estimated": []}))

    def test_real_handshake_smoke_optional(self):
        # only runs when `codegraph` is on PATH; skipped otherwise
        import shutil
        if not shutil.which("codegraph"):
            self.skipTest("codegraph not installed")
        r = mcp_client.list_tools("codegraph", ["serve", "--mcp"], timeout=20)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertGreaterEqual(len(r["tools"]), 1)


if __name__ == "__main__":
    unittest.main()
