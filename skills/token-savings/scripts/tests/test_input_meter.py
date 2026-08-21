"""Session-level input meter (v9)."""
import unittest

from toks import input_meter


class TestInputMeter(unittest.TestCase):
    def test_clean_transcript(self):
        m = input_meter.meter("short one\n\nshort two\n")
        self.assertEqual(m["actual_tok"], m["actual_chars"] // 4)
        self.assertEqual(m["repeat_chars"], 0)

    def test_repeat_detected(self):
        big = "x" * 300
        m = input_meter.meter(big + "\n\n" + big)
        self.assertGreater(m["repeat_chars"], 0)
        self.assertGreater(m["recoverable_pct"], 0)

    def test_format_report(self):
        rep = input_meter.format_report(input_meter.meter("a\n\nb\n"))
        self.assertIn("input-meter:", rep)
        self.assertIn("repeat content", rep)


if __name__ == "__main__":
    unittest.main()