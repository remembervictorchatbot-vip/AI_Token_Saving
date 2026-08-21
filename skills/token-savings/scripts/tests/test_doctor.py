"""Environment doctor (v10) - autopilot wiring self-check."""
import unittest

from toks import doctor


class TestDoctor(unittest.TestCase):
    def test_checks_have_required_shape(self):
        checks = doctor.run_checks()
        self.assertGreaterEqual(len(checks), 4)
        for c in checks:
            self.assertIn("check", c)
            self.assertIn("status", c)
            self.assertIn("detail", c)
            self.assertIn(c["status"], ("ok", "warn", "missing"))

    def test_python_always_ok(self):
        checks = doctor.run_checks()
        py = [c for c in checks if c["check"] == "python"]
        self.assertEqual(py[0]["status"], "ok")

    def test_format_report(self):
        rep = doctor.format_report(doctor.run_checks())
        self.assertIn("toks doctor", rep)
        self.assertIn("checks OK", rep)


if __name__ == "__main__":
    unittest.main()