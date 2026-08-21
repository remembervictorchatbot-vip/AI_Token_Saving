"""Edge cases: empty/whitespace/binary/giant-input/nested-refs/unicode."""
import os
import tempfile
import unittest

from toks import dedup, astrip, safemode, measure, checkpoint, protect


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.cache = dedup.DedupCache(cache_path=os.path.join(tempfile.mkdtemp(), "d.json"))

    def test_empty_string_dedup(self):
        self.assertIsNone(self.cache.ref(""))
        self.assertIsNotNone(self.cache.ref(""))

    def test_single_char(self):
        self.assertIsNone(self.cache.ref("x"))
        self.assertIn("x", astrip.astrip("x = 1", lang="py") or "x")

    def test_whitespace_only(self):
        self.assertIsNone(self.cache.ref("   \n  "))
        self.assertIsNotNone(self.cache.ref("   \n  "))

    def test_gibberish_python_falls_back(self):
        # not valid python, not a comment line -> regex skeleton fallback, no crash
        out = astrip.astrip("¥£© ~~~ @@@ not code §", lang="py")
        self.assertIn("skeleton fallback", out)

    def test_extremely_long_single_line(self):
        big = "a" * 100000
        out = astrip.astrip(f"def f():\n    return '{big}'\n", lang="py")
        self.assertIn("def f(", out)

    def test_nested_refs_is_ref(self):
        tok = "§ref:abc123§"
        self.assertEqual(dedup.is_ref(tok), "abc123")
        self.assertIsNone(dedup.is_ref("§ref:§"))  # too short

    def test_overlapping_protected_zones(self):
        b = "[[KEEP]]outer [[KEEP]]inner[[/KEEP]] tail[[/KEEP]]"
        regs = measure.extract_protected(b)
        self.assertTrue(any("inner" in r for r in regs))

    def test_unicode_identifiers_astrip(self):
        code = "def 計算(a):\n    return a\n"
        out = astrip.astrip(code, lang="py")
        self.assertIn("計算", out)

    def test_safemode_empty(self):
        self.assertEqual(safemode.risk_level(""), "safe")

    def test_checkpoint_empty_state(self):
        blk = checkpoint.emit_checkpoint({})
        parsed = checkpoint.parse_checkpoint(blk)
        self.assertEqual(parsed.get("Active task"), "(none)")

    def test_protect_with_binary_blob(self):
        # placeholder uses NUL bytes; ensure a real NUL in content doesn't corrupt
        text = "data \x00 here [[KEEP]]K[[/KEEP]] end"
        out = protect.compress_protected(text, lambda t: t)
        self.assertIn("K", out)


if __name__ == "__main__":
    unittest.main()
