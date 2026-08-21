"""Quality gate - protected zones must survive every compression."""
import unittest

from toks import measure


class TestQualityGate(unittest.TestCase):
    def test_protected_survives(self):
        b = "x [[KEEP]]SECRET_ID_123[[/KEEP]] y"
        q = measure.quality_gate(b, b)
        self.assertTrue(q["pass"])
        self.assertEqual(q["checked"], 1)

    def test_protected_missing(self):
        b = "x [[KEEP]]SECRET_ID_123[[/KEEP]] y"
        q = measure.quality_gate(b, "x y")
        self.assertFalse(q["pass"])
        self.assertEqual(len(q["missing"]), 1)

    def test_multiple_zones(self):
        b = "[[KEEP]]a[[/KEEP]] mid [[KEEP]]b[[/KEEP]]"
        q = measure.quality_gate(b, b)
        self.assertTrue(q["pass"])
        self.assertEqual(q["checked"], 2)

    def test_extra_protected(self):
        q = measure.quality_gate("hello world", "hello", extra_protected=["world"])
        self.assertFalse(q["pass"])

    def test_extract(self):
        regs = measure.extract_protected("a [[KEEP]]x[[/KEEP]] b")
        self.assertEqual(regs, ["x"])

    def test_nested_zones(self):
        b = "[[KEEP]]outer [[KEEP]]inner[[/KEEP]] tail[[/KEEP]]"
        regs = measure.extract_protected(b)
        self.assertTrue(any("inner" in r for r in regs))


if __name__ == "__main__":
    unittest.main()
