"""Durable RESUME.md checkpoint — fixes D1 (continuity never fired)."""
import os
import tempfile
import unittest

from toks import resume


class TestResume(unittest.TestCase):
    def test_write_read_roundtrip(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "RESUME.md")
        resume.write_resume(
            {"Active task": "T", "Lessons to carry": ["l1"], "Open questions": ["q1"]},
            path=p,
        )
        data = resume.read_resume(p)
        self.assertEqual(data.get("Active task"), "T")
        self.assertIn("l1", data.get("Lessons to carry", ""))
        self.assertIn("q1", data.get("Open questions", ""))

    def test_missing_returns_empty(self):
        self.assertEqual(resume.read_resume("/nonexistent/path/RESUME.md"), {})

    def test_has_open_work(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "RESUME.md")
        resume.write_resume({"Active task": "Open task", "Next steps": ["n1"]}, path=p)
        self.assertTrue(resume.has_open_work(p))
        p2 = os.path.join(d, "R2.md")
        resume.write_resume({}, path=p2)
        self.assertFalse(resume.has_open_work(p2))
