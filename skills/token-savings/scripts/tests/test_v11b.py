"""Tests for v11b: read_cache (re-read suppression) + memory_decay."""
import os
import tempfile
import time
import unittest

from toks import read_cache, memory_decay


class TestReadCache(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "f.txt")
        with open(self.path, "w") as fh:
            fh.write("hello world\n" * 10)
        self.cache_file = os.path.join(self.dir, ".cache.json")

    def test_miss_then_hit(self):
        rc = read_cache.ReadCache(self.cache_file)
        self.assertEqual(rc.check(self.path)["verdict"], "MISS")  # never recorded
        rc.record(self.path)
        self.assertEqual(rc.check(self.path)["verdict"], "HIT")

    def test_change_invalidates(self):
        rc = read_cache.ReadCache(self.cache_file)
        rc.record(self.path)
        time.sleep(0.01)
        with open(self.path, "w") as fh:
            fh.write("different content entirely\n")
        self.assertEqual(rc.check(self.path)["verdict"], "MISS")

    def test_missing_path(self):
        rc = read_cache.ReadCache(self.cache_file)
        self.assertEqual(rc.check(os.path.join(self.dir, "nope.txt"))["verdict"], "MISS")

    def test_report_hit_mentions_skip(self):
        self.assertIn("skip re-read", read_cache.format_report(
            {"verdict": "HIT", "reason": "mtime+hash unchanged", "saved_chars_hint": 100}))


class TestMemoryDecay(unittest.TestCase):
    def test_completed_entry_demoted(self):
        res = memory_decay.audit_memory("## Old task\nFixed the login bug. Done.\n")
        self.assertEqual(res["entries"][0]["action"], "DEMOTE")

    def test_todo_kept(self):
        res = memory_decay.audit_memory("## Current work\nTODO: refactor parser (in progress)\n")
        self.assertNotEqual(res["entries"][0]["action"], "DEMOTE")

    def test_bloated_hot_entry_compress(self):
        body = ("Active convention. " * 40).strip()
        res = memory_decay.audit_memory("## Conventions\n" + body + "\n", max_chars=400)
        self.assertEqual(res["entries"][0]["action"], "COMPRESS")

    def test_small_recent_entry_kept(self):
        res = memory_decay.audit_memory("## Style\nPrefer CDec in VBA math.\n")
        self.assertEqual(res["entries"][0]["action"], "KEEP")

    def test_recoverable_pct_positive_when_stale_present(self):
        text = ("## A\nDone and shipped last release.\n\n## B\nKeep: active rule.\n")
        res = memory_decay.audit_memory(text)
        self.assertGreaterEqual(res["demotable_pct"], 0.0)

    def test_report_renders(self):
        self.assertIn("memory-decay audit", memory_decay.format_report(
            memory_decay.audit_memory("## X\nhi\n")))


if __name__ == "__main__":
    unittest.main()
