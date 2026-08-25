"""Tests for v11d tool-search surface (toolsearch.py)."""
import unittest

from toks import toolsearch

MANIFEST = {
    "connectors": [
        {"name": "github", "tools": [
            {"name": "create_pull_request", "schema_chars": 1200,
             "desc": "Create a pull request on a repository"},
            {"name": "list_issues", "schema_chars": 900,
             "desc": "List issues in a repository"},
        ]},
        {"name": "email", "tools": [
            {"name": "send_email", "schema_chars": 1500,
             "desc": "Send an email via SMTP"},
        ]},
    ]
}


class TestToolSearch(unittest.TestCase):
    def test_build_index_one_line_per_tool(self):
        idx = toolsearch.build_index(MANIFEST)
        lines = [ln for ln in idx.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("github.create_pull_request —"))

    def test_plan_defer_counts(self):
        plan = toolsearch.plan_defer(MANIFEST, keep=["send_email"], max_upfront=2)
        self.assertEqual(plan["total_tools"], 3)
        self.assertLessEqual(len(plan["upfront"]), 2 + 1)  # keep + fill
        self.assertGreater(plan["saved_pct"], 0.0)

    def test_plan_tokens_after_less_than_before(self):
        plan = toolsearch.plan_defer(MANIFEST, max_upfront=1)
        self.assertLess(plan["tokens_after"], plan["tokens_before"])

    def test_search_finds_relevant_tool(self):
        hits = toolsearch.search_tools(MANIFEST, "send an email")
        self.assertIn("email.send_email", hits)

    def test_search_no_match_empty(self):
        self.assertEqual(toolsearch.search_tools(MANIFEST, "zzz qqq"), [])

    def test_index_line_budget_respected(self):
        from toks.toolaudit import _tokens_for
        idx = toolsearch.build_index(MANIFEST)
        self.assertLess(len(idx) // 4, _tokens_for(
            [t for c in MANIFEST["connectors"] for t in c["tools"]]))

    def test_report_renders(self):
        plan = toolsearch.plan_defer(MANIFEST, max_upfront=1)
        self.assertIn("tool-search surface plan", toolsearch.estimate_report(plan))


if __name__ == "__main__":
    unittest.main()
