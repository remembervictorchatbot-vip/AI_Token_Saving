"""Tests for v11 commands: pd (progressive disclosure), route (tier routing),
isolate (sub-agent context isolation)."""
import unittest

from toks import pd, route, isolate


class TestPD(unittest.TestCase):
    def test_security_never_defers(self):
        text = "# Security\nNEVER commit secrets or credentials. MUST run scanner.\n"
        res = pd.audit_prompt(text)
        self.assertEqual(res["l2_sections"], [])

    def test_history_narrative_extracts(self):
        text = ("# Rule X\nKeep the flag on.\n# Why Rule X exists\n"
                "This rule exists because we once deployed a broken build.\n")
        res = pd.audit_prompt(text)
        self.assertTrue(any("Why Rule X" in s["section"] for s in res["l2_sections"]))

    def test_big_table_extracts(self):
        rows = "\n".join("| k%d | v%d |" % (i, i) for i in range(6))
        text = "# Env Vars\n| name | value |\n|---|---|\n" + rows + "\n"
        res = pd.audit_prompt(text)
        self.assertEqual(len(res["l2_sections"]), 1)

    def test_savings_positive_on_layered_prompt(self):
        body = "Operational: run the checks.\n"
        filler = "\n".join("- item %d" % i for i in range(20))
        text = "# Core\n" + body + "\n# Full inventory\n" + filler + "\n"
        res = pd.audit_prompt(text)
        self.assertGreater(res["saved_pct"], 0.0)

    def test_report_renders(self):
        self.assertIn("progressive-disclosure audit", pd.format_report(pd.audit_prompt("# A\nhi\n")))

    def test_cli_pd_file(self):
        from toks import cli
        ns = cli.build_parser().parse_args(["pd", "--text", "# A\nhello\n"])
        cli.handle_pd(ns)  # smoke: no exception


class TestRoute(unittest.TestCase):
    def test_mechanical(self):
        self.assertEqual(route.classify("reformat this file and fix lint typos"), "mechanical")

    def test_reasoning(self):
        self.assertEqual(route.classify("design the security architecture with tradeoffs"), "reasoning")

    def test_default_pattern_matching(self):
        self.assertEqual(route.classify("add a button to the settings page"), "pattern-matching")

    def test_estimate_saves_vs_top_tier(self):
        res = route.estimate("rename variable x to y", top_tier="reasoning")
        self.assertGreater(res["saved_pct"], 0.0)
        self.assertEqual(res["tier"], "mechanical")


class TestIsolate(unittest.TestCase):
    def test_minimal_brief_no_leak(self):
        res = isolate.build_brief(goal="Fix bug in parser.", paths="a.py,b.py,a.py ")
        self.assertIn("a.py", res["paths"])
        self.assertNotIn("a.py, a.py", res["brief"])
        self.assertEqual(res["warnings"], [])

    def test_history_leak_flagged(self):
        res = isolate.build_brief(goal="As we discussed earlier in this session, do it.")
        self.assertTrue(any(w.startswith("history-leak") for w in res["warnings"]))

    def test_state_dump_flagged(self):
        res = isolate.build_brief(goal="Do it.", context="\n".join("line %d" % i for i in range(400)))
        self.assertTrue(any(w.startswith("state-dump") for w in res["warnings"]))

    def test_dedupes_context_lines(self):
        ctx = "alpha\nalpha\nbeta\n"
        res = isolate.build_brief(goal="g", context=ctx)
        self.assertEqual(res["brief"].count("alpha"), 1)


if __name__ == "__main__":
    unittest.main()
