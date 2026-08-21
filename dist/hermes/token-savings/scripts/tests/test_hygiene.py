"""Context hygiene checks (file size / tab / thread cadence)."""
import os
import tempfile
import unittest

from toks import hygiene


class TestHygiene(unittest.TestCase):
    def test_over_limit(self):
        r = hygiene.hygiene_report(lines=400)
        self.assertTrue(r["over_limit"])
        self.assertTrue(r["recommend_split"])

    def test_under_limit(self):
        r = hygiene.hygiene_report(lines=200)
        self.assertFalse(r["over_limit"])
        self.assertFalse(r["recommend_split"])

    def test_missing(self):
        r = hygiene.hygiene_report(lines=-1)
        self.assertIsNone(r["over_limit"])
        self.assertFalse(r["recommend_split"])

    def test_fresh_thread_window(self):
        r = hygiene.hygiene_report(lines=100)
        self.assertEqual(r["fresh_thread_every"], "8-10 turns")
        self.assertTrue(r["close_unused_tabs"])

    def test_file_read(self):
        p = os.path.join(tempfile.gettempdir(), "hyg_test.py")
        with open(p, "w") as f:
            f.write("\n".join([f"x{i}=1" for i in range(350)]))
        r = hygiene.hygiene_report(path=p)
        self.assertEqual(r["lines"], 350)
        self.assertTrue(r["recommend_split"])
        os.remove(p)


if __name__ == "__main__":
    unittest.main()
