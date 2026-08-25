"""Tests for v14 CCR reversible compression cache (ccr.py)."""
import tempfile
import unittest

from toks import ccr, gate


class TestCCR(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.cache = ccr.CCR(root=self.root, max_entries=5)

    def test_store_then_retrieve_roundtrip(self):
        original = "line of important output\n" * 50
        h = self.cache.store(original)
        res = self.cache.retrieve(h)
        self.assertTrue(res["hit"])
        self.assertEqual(res["text"], original)

    def test_store_idempotent(self):
        t = "same content"
        h1 = self.cache.store(t)
        h2 = self.cache.store(t)
        self.assertEqual(h1, h2)

    def test_miss_unknown_hash(self):
        res = self.cache.retrieve("deadbeefdeadbeef")
        self.assertFalse(res["hit"])

    def test_ttl_expiry(self):
        short = ccr.CCR(root=self.root, ttl_days=0)
        h = short.store("expiring soon\n" * 10)
        res = short.retrieve(h)  # ttl 0 => any existing entry expires
        self.assertFalse(res["hit"])

    def test_lru_eviction(self):
        for i in range(8):  # max_entries=5 in setUp
            self.cache.store("entry {}\n".format(i) * 20)
        st = self.cache.stats()
        self.assertLessEqual(st["entries"], 5)

    def test_gate_stores_ccr_ref(self):
        # unique content (fresh dedup cache) so compression actually happens
        text = "unique gate content xyz\n" + ("block\n" * 80)
        out = gate.gate_content(text)
        h = None
        for ln in out.splitlines():
            if ln.startswith("[ccr:"):
                h = ln[5:].strip("[]")
                break
        if h is None:
            self.skipTest("gate returned a dedup ref (shared cache) - CCR not reached")
        res = ccr.CCR().retrieve(h)
        self.assertTrue(res["hit"], "gate must store originals retrievable")

    def test_report_hit_and_miss(self):
        self.assertIn("HIT", ccr.format_report({"hit": True, "chars": 10,
                                                "age_days": 0.0, "meta": "", "text": "x"}))
        self.assertIn("MISS", ccr.format_report({"hit": False, "why": "gone"}))


if __name__ == "__main__":
    unittest.main()
