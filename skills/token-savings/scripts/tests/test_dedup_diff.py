"""Delta re-read (v8) - dedup --diff: ref on exact repeat, hunks on change."""
import os
import tempfile
import unittest

from toks import dedup


class TestDedupDiff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dc = dedup.DedupCache(cache_path=os.path.join(self.tmp, "dedup.json"))

    def test_first_occurrence_none(self):
        self.assertIsNone(self.dc.diff_ref("line one\nline two\n"))

    def test_exact_repeat_is_ref(self):
        self.dc.diff_ref("alpha\nbeta\n")
        r = self.dc.diff_ref("alpha\nbeta\n")
        self.assertTrue(r.startswith(dedup.REF_OPEN))

    def test_changed_content_returns_diff_hunks(self):
        self.dc.diff_ref("line one\nline two\nline three\n")
        r = self.dc.diff_ref("line one\nline TWO changed\nline three\n")
        self.assertTrue(r.startswith(dedup.DIFF_OPEN))
        self.assertIn("-line two", r)
        self.assertIn("+line TWO changed", r)
        # unchanged lines are NOT emitted (n=0 hunks)
        self.assertNotIn("line one", r)
        self.assertNotIn("line three", r)

    def test_diff_header_contains_new_hash(self):
        self.dc.diff_ref("aaa\n")
        r = self.dc.diff_ref("bbb\n")
        new_h = dedup.content_hash("bbb\n")
        self.assertIn(new_h, r)

    def test_reverts_to_ref_after_change(self):
        self.dc.diff_ref("aaa\n")
        self.dc.diff_ref("bbb\n")          # diff
        r = self.dc.diff_ref("bbb\n")      # now exact repeat of latest
        self.assertTrue(r.startswith(dedup.REF_OPEN))

    def test_stats_tracks_latest(self):
        self.dc.diff_ref("aaa\n")
        self.dc.diff_ref("bbb\n")
        s = self.dc.stats()
        self.assertEqual(s["latest"], dedup.content_hash("bbb\n"))
        self.assertEqual(s["entries"], 2)

    def test_unicode_diff(self):
        self.dc.diff_ref("中文一行\n第二行\n")
        r = self.dc.diff_ref("中文一行\n第二行变了\n")
        self.assertTrue(r.startswith(dedup.DIFF_OPEN))
        self.assertIn("第二行变了", r)


if __name__ == "__main__":
    unittest.main()