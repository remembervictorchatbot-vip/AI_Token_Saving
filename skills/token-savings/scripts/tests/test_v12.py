"""Tests for v12 discover (live tool-surface discovery)."""
import json
import os
import tempfile
import unittest
from unittest import mock

from toks import discover


class TestDiscover(unittest.TestCase):
    def test_from_claude_code_parses_servers(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump({"projects": {"x": {"mcpServers": {
                "alpha": {"command": "a"}, "beta": {"command": "b"}}}}}, fh)
            path = fh.name
        try:
            with mock.patch.object(discover.os.path, "expanduser", return_value=path):
                names = [c["name"] for c in discover._from_claude_code()]
            self.assertIn("alpha", names)
        finally:
            os.unlink(path)

    def test_missing_file_returns_empty(self):
        with mock.patch.object(discover.os.path, "expanduser",
                               return_value="/nonexistent/x.json"):
            self.assertEqual(discover._from_claude_code(), [])

    def test_hermes_yaml_parse(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as fh:
            fh.write("other: 1\nmcp_servers:\n  codegraph:\n    enabled: true\n  feishu:\n")
            path = fh.name
        try:
            with mock.patch.object(discover.os.path, "expanduser", return_value=path):
                names = [c["name"] for c in discover._from_hermes()]
            self.assertEqual(names, ["codegraph", "feishu"])
        finally:
            os.unlink(path)

    def test_discover_dedupes(self):
        with mock.patch.object(discover, "_from_claude_code",
                               return_value=[{"name": "x"}]), \
             mock.patch.object(discover, "_from_hermes",
                               return_value=[{"name": "x"}, {"name": "y"}]):
            m = discover.discover()
        names = [c["name"] for c in m["connectors"]]
        self.assertEqual(names, ["x", "y"])

    def test_report_renders(self):
        r = discover.format_report({"connectors": [
            {"name": "a", "tool_count": 10, "avg_schema_chars": 900}]})
        self.assertIn("discovered connectors", r)


if __name__ == "__main__":
    unittest.main()
