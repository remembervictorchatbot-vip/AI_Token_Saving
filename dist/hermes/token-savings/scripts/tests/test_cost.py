"""Input-side cost preflight (v8) - estimate before execute."""
import unittest

from toks import cost


class TestCost(unittest.TestCase):
    def test_est_tokens_chars_div_4(self):
        self.assertEqual(cost.est_tokens("abcd"), 1)
        self.assertEqual(cost.est_tokens("abcdefgh"), 2)

    def test_estimate_math(self):
        e = cost.estimate(steps=3, ctx_chars=4000, out_chars=4000,
                          price_per_mtok=1.0, peak=True)
        self.assertEqual(e["uncached_in_tok"], 1000)
        self.assertEqual(e["cached_in_tok"], 3000)
        self.assertEqual(e["output_tok"], 1000)
        self.assertEqual(e["total_tok"], 5000)
        # peak 2x: 5000 / 1e6 * 1.0 * 2 = 0.01
        self.assertAlmostEqual(e["cost"], 0.01)

    def test_idle_is_quarter_of_peak(self):
        peak = cost.estimate(steps=1, ctx_chars=4000, out_chars=0,
                             price_per_mtok=2.0, peak=True)
        idle = cost.estimate(steps=1, ctx_chars=4000, out_chars=0,
                             price_per_mtok=2.0, peak=False)
        self.assertAlmostEqual(idle["cost"], peak["cost"] / 4.0)

    def test_steps_floor_is_one(self):
        e = cost.estimate(steps=0, ctx_chars=4000, out_chars=0)
        self.assertEqual(e["steps"], 1)

    def test_format_report_contains_terms(self):
        e = cost.estimate(steps=2, ctx_chars=4000, out_chars=0)
        rep = cost.format_report(e)
        self.assertIn("cost-estimate:", rep)
        self.assertIn("cached re-read", rep)
        self.assertIn("TOTAL", rep)

        self.assertIn("IDLE", cost.format_report(cost.estimate(steps=1, ctx_chars=1, peak=False)))


if __name__ == "__main__":
    unittest.main()