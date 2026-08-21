"""compress_protected - [[KEEP]] zones survive ANY compressor (the quality promise)."""
import json
import unittest

from toks import protect, compress, astrip, measure


class TestProtect(unittest.TestCase):
    def test_survives_astrip(self):
        # KEEP zone lives in an assignment (not a comment) so it survives AST parsing
        code = 'ID_LINE = "[[KEEP]]ID_123[[/KEEP]]"\n\ndef f(x):\n    return x\n'
        out = protect.compress_protected(code, lambda t: astrip.astrip(t, lang="py"))
        self.assertIn("ID_123", out)

    def test_survives_json(self):
        payload = json.dumps(
            {"a": 1, "note": "[[KEEP]]src#9[[/KEEP]]", "debug": "x"}
        )
        out = protect.compress_protected(
            payload, lambda t: compress.compress_json(json.loads(t))
        )
        self.assertIn("src#9", out)
        self.assertNotIn("debug", out)

    def test_no_zones_passthrough(self):
        code = "def f():\n    pass\n"
        out = protect.compress_protected(code, lambda t: astrip.astrip(t, lang="py"))
        self.assertIn("def f", out)

    def test_quality_gate_after(self):
        text = "x [[KEEP]]Z[[/KEEP]] y"
        out = protect.compress_protected(text, lambda t: t)
        q = measure.quality_gate(text, out)
        self.assertTrue(q["pass"])

    def test_multiple_zones(self):
        text = "[[KEEP]]one[[/KEEP]] and [[KEEP]]two[[/KEEP]]"
        out = protect.compress_protected(text, lambda t: t)
        self.assertIn("one", out)
        self.assertIn("two", out)


if __name__ == "__main__":
    unittest.main()
