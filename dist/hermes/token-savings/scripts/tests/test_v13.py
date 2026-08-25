"""Tests for v13 one-command auto sweep (full_auto.py)."""
import unittest

from toks import full_auto


class TestFullAuto(unittest.TestCase):
    def test_report_renders_header(self):
        res = {"doctor": [], "tools": None, "skills": None, "issues": []}
        self.assertIn("[toks auto] full-auto sweep", full_auto.format_report(res))

    def test_directives_nothing_when_clean(self):
        res = {"doctor": [{"check": "python", "status": "ok", "detail": "", "fix": ""}],
               "tools": None,
               "skills": {"count": 1, "index_tok": 30, "total_tok": 100},
               "issues": []}
        r = full_auto.format_report(res)
        self.assertIn("nothing - all surfaces clean", r)

    def test_directives_include_dupes_and_wiring(self):
        res = {
            "doctor": [{"check": "input filter", "status": "warn",
                        "detail": "off", "fix": "export TOKS_UPSTREAM=x"}],
            "tools": {"connectors": 1, "live": 0, "estimated": 1,
                      "audit": {"total_est_tokens_per_call": 5000,
                                "review_candidates": ["big"]}},
            "skills": {"count": 5, "index_tok": 100, "total_tok": 9000},
            "issues": [{"type": "NEAR-DUP", "skill": "b", "detail": "dup of a"},
                       {"type": "OVERSIZED", "skill": "c", "detail": "600 ln"}],
        }
        r = full_auto.format_report(res)
        self.assertIn("export TOKS_UPSTREAM=x", r)
        self.assertIn("merge/archive duplicate skills: b", r)
        self.assertIn("slim oversized SKILL.mds", r)
        self.assertIn("prune tool surfaces: big", r)

    def test_tools_error_degrades(self):
        res = {"doctor": [], "tools": {"error": "boom"}, "skills": None, "issues": []}
        r = full_auto.format_report(res)
        self.assertIn("unavailable (boom)", r)

    def test_os_skills_root_is_path(self):
        self.assertIsInstance(full_auto.os_skills_root(), str)


if __name__ == "__main__":
    unittest.main()
