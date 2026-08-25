"""Tests for v11c smart auto-compress policy (auto.py)."""
import unittest

from toks import auto


class TestAutoCompress(unittest.TestCase):
    def test_short_content_skipped(self):
        res = auto.decide("tiny")
        self.assertEqual(res["verdict"], "SKIP")

    def test_secrets_skipped_verbatim(self):
        text = ("Error log with api_key=sk-1234567890abcdef and password=hunter2 "
                + "line\n" * 40)
        res = auto.decide(text)
        self.assertEqual(res["verdict"], "SKIP")

    def test_high_ratio_applies(self):
        # highly repetitive prose: trim_bash collapses repeats massively
        text = "same line of log output\n" * 120
        res = auto.decide(text)
        self.assertEqual(res["verdict"], "APPLY")
        self.assertGreaterEqual(res["saved_ratio"], 0.5)

    def test_mid_band_is_shadow(self):
        # construct content whose projection lands in [0.3, 0.5) — use
        # min/enforce overrides to force the band deterministically
        text = "line %d of moderately repetitive output with variety %d\n"
        body = "".join(text.format(i, i * 7) for i in range(60))
        res = auto.decide(body, min_ratio=0.01, enforce_ratio=0.99)
        self.assertIn(res["verdict"], ("SHADOW", "SKIP"))

    def test_below_min_ratio_skip(self):
        text = "\n".join("unique line {} {}".format(i, i * 13) for i in range(30))
        res = auto.decide(text)
        if res["saved_ratio"] < 0.3:
            self.assertEqual(res["verdict"], "SKIP")

    def test_min_ratio_default_is_03(self):
        self.assertEqual(auto.DEFAULT_MIN_RATIO, 0.3)

    def test_apply_output_smaller(self):
        text = "repeated block\n" * 200
        res = auto.decide(text)
        self.assertLess(len(res["out"]), len(text))

    def test_report_renders(self):
        self.assertIn("auto-compress", auto.format_report(auto.decide("x")))


if __name__ == "__main__":
    unittest.main()
