"""Connector tool-surface audit (USE-7): recommend-only, never disconnects."""
import unittest

from toks import toolaudit


SAMPLE = {
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
}


class TestParseManifest(unittest.TestCase):
    def test_tools_list_form(self):
        cs = toolaudit.parse_manifest(SAMPLE)
        self.assertEqual(len(cs), 4)
        kdocs = next(c for c in cs if c["name"] == "kdocs")
        self.assertEqual(len(kdocs["tools"]), 3)

    def test_flat_form_expands(self):
        cs = toolaudit.parse_manifest(SAMPLE)
        feishu = next(c for c in cs if c["name"] == "feishu")
        self.assertEqual(len(feishu["tools"]), 60)

    def test_accepts_json_string(self):
        import json
        cs = toolaudit.parse_manifest(json.dumps(SAMPLE))
        self.assertEqual(len(cs), 4)

    def test_rejects_invalid_manifest(self):
        with self.assertRaises(ValueError):
            toolaudit.parse_manifest({})
        with self.assertRaises(ValueError):
            toolaudit.parse_manifest("{}")
        with self.assertRaises(ValueError):
            toolaudit.parse_manifest([1, 2, 3])


class TestAudit(unittest.TestCase):
    def test_total_tokens(self):
        res = toolaudit.audit_connectors(SAMPLE)
        # kdocs: 450+375+400, feishu: 60*300, notion: 12*225, agent-mail: 8*175
        self.assertEqual(res["total_est_tokens_per_call"], 1225 + 18000 + 2700 + 1400)
        self.assertEqual(res["connector_count"], 4)

    def test_ranks_by_cost_desc(self):
        res = toolaudit.audit_connectors(SAMPLE)
        toks = [r["est_tokens_per_call"] for r in res["rows"]]
        self.assertEqual(toks, sorted(toks, reverse=True))
        self.assertEqual(res["rows"][0]["name"], "feishu")

    def test_flags_over_threshold_as_review(self):
        res = toolaudit.audit_connectors(SAMPLE)
        self.assertIn("feishu", res["review_candidates"])
        self.assertNotIn("agent-mail", res["review_candidates"])

    def test_abs_floor_flags_smaller_connectors(self):
        res = toolaudit.audit_connectors(SAMPLE, abs_token_floor=2000)
        self.assertIn("notion", res["review_candidates"])

    def test_keep_list_exempts(self):
        res = toolaudit.audit_connectors(SAMPLE, keep=["feishu"])
        self.assertNotIn("feishu", res["review_candidates"])
        self.assertEqual(
            next(r for r in res["rows"] if r["name"] == "feishu")["recommendation"],
            "keep (explicit)",
        )

    def test_never_disconnects(self):
        res = toolaudit.audit_connectors(SAMPLE)
        self.assertFalse(res["disconnected_any"])
        self.assertTrue(all(r["auto_disconnected"] is False for r in res["rows"]))


class TestReport(unittest.TestCase):
    def test_report_is_recommend_only(self):
        res = toolaudit.audit_connectors(SAMPLE)
        rep = toolaudit.format_report(res)
        self.assertIn("recommend-only", rep)
        self.assertIn("never disconnects", rep)
        self.assertIn("feishu", rep)

    def test_report_empty_when_no_candidates(self):
        tiny = {"connectors": [
            {"name": "a", "tool_count": 2, "avg_schema_chars": 100},
            {"name": "b", "tool_count": 2, "avg_schema_chars": 100},
        ]}
        res = toolaudit.audit_connectors(tiny, threshold_pct=100.0)
        self.assertEqual(res["review_candidates"], [])
        rep = toolaudit.format_report(res)
        self.assertIn("No prune candidates", rep)


if __name__ == "__main__":
    unittest.main()
