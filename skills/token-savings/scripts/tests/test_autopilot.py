"""Session autopilot (v10) - meter + audit + gate in one pass."""
import unittest

from toks import autopilot


class TestAutopilot(unittest.TestCase):
    def test_clean_session(self):
        r = autopilot.autopilot("short reply\n\nsecond reply\n")
        self.assertEqual(r["findings"], [])
        self.assertTrue(r["gate"]["pass"])

    def test_dirty_session_finds_issues(self):
        big = "x" * 300
        r = autopilot.autopilot(big + "\n\n" + big + "\n\nrun task\nrun task\nrun task\n")
        self.assertTrue(any(f["rule"] == "re-read" for f in r["findings"]))
        self.assertTrue(any(f["rule"] == "loop" for f in r["findings"]))

    def test_format_directives(self):
        rep = autopilot.format_directives(autopilot.autopilot("a\n\nb\n"))
        self.assertIn("[autopilot]", rep)
        self.assertIn("NEXT-TURN DIRECTIVES", rep)
        self.assertIn("input :", rep)
        self.assertIn("output:", rep)

    def test_empty_session(self):
        r = autopilot.autopilot("")
        self.assertTrue(r["gate"]["pass"])


if __name__ == "__main__":
    unittest.main()