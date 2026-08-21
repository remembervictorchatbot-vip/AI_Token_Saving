"""Deduplication via file-hash caching - the single largest token win."""
import os
import tempfile
import unittest

from toks import dedup


class TestDedup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache = os.path.join(self.tmp, "dedup.json")
        self.dc = dedup.DedupCache(cache_path=self.cache)

    def test_first_occurrence_is_none(self):
        self.assertIsNone(self.dc.ref("hello world"))

    def test_second_occurrence_is_ref(self):
        r1 = self.dc.ref("hello world")
        r2 = self.dc.ref("hello world")
        self.assertIsNone(r1)
        self.assertIsNotNone(r2)
        self.assertTrue(r2.startswith(dedup.REF_OPEN))
        self.assertTrue(r2.endswith(dedup.REF_CLOSE))

    def test_distinct_content_distinct_refs(self):
        self.dc.ref("alpha")
        self.dc.ref("alpha")
        self.dc.ref("beta")
        self.dc.ref("beta")
        ra = self.dc.ref("alpha")
        rb = self.dc.ref("beta")
        self.assertNotEqual(ra, rb)

    def test_content_hash_stable(self):
        self.assertEqual(dedup.content_hash("x"), dedup.content_hash("x"))
        self.assertNotEqual(dedup.content_hash("x"), dedup.content_hash("y"))

    def test_is_ref(self):
        self.assertIsNone(dedup.is_ref("not a ref"))
        # REF_OPEN + REF_CLOSE with no hash is too short -> None
        self.assertIsNone(dedup.is_ref(dedup.REF_OPEN + dedup.REF_CLOSE))
        h = "abc123"
        tok = f"{dedup.REF_OPEN}{h}{dedup.REF_CLOSE}"
        self.assertEqual(dedup.is_ref(tok), h)

    def test_expand_returns_preview(self):
        self.dc.ref("SELECT * FROM users WHERE id = 1")
        ref = self.dc.ref("SELECT * FROM users WHERE id = 1")
        self.assertIn("SELECT", self.dc.expand(ref))

    def test_stats(self):
        self.dc.ref("a")
        self.dc.ref("a")
        self.dc.ref("b")
        s = self.dc.stats()
        self.assertEqual(s["stored"], 2)
        self.assertEqual(s["hits"], 1)
        self.assertEqual(s["entries"], 2)

    def test_empty_string(self):
        self.assertIsNone(self.dc.ref(""))
        self.assertIsNotNone(self.dc.ref(""))  # same hash -> ref

    def test_unicode(self):
        txt = "中文内容 こんにちは émojis 🚀"
        self.assertIsNone(self.dc.ref(txt))
        self.assertIsNotNone(self.dc.ref(txt))

    def test_large_content(self):
        big = "x" * 100000
        self.assertIsNone(self.dc.ref(big))
        self.assertIsNotNone(self.dc.ref(big))

    def test_reset(self):
        self.dc.ref("z")
        self.dc.reset()
        self.assertEqual(self.dc.stats()["entries"], 0)
        self.assertIsNone(self.dc.ref("z"))  # first again


if __name__ == "__main__":
    unittest.main()
