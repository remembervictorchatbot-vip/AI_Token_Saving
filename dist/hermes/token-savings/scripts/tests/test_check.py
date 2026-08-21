"""O-6 validate-then-emit gate (v8)."""
import unittest

from toks import check


class TestCheck(unittest.TestCase):
    def test_valid_py(self):
        ok, _ = check.validate("def f():\n    return 1\n", lang="py")
        self.assertTrue(ok)

    def test_invalid_py(self):
        ok, msg = check.validate("def broken(:\n", lang="py")
        self.assertFalse(ok)
        self.assertIn("INVALID", msg)

    def test_valid_json(self):
        ok, _ = check.validate('{"a": 1}', lang="json")
        self.assertTrue(ok)

    def test_invalid_json(self):
        ok, _ = check.validate('{"a": 1,}', lang="json")
        self.assertFalse(ok)

    def test_md_balanced_fences(self):
        self.assertTrue(check.validate("```py\nx=1\n```", lang="md")[0])
        self.assertFalse(check.validate("```py\nx=1", lang="md")[0])


if __name__ == "__main__":
    unittest.main()