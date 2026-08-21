"""Safe-mode classifier - refuse to compress secrets / stack traces."""
import unittest

from toks import safemode


class TestSafeMode(unittest.TestCase):
    def test_secret_api_key(self):
        self.assertEqual(safemode.risk_level("api_key = 'ABCDEFGH12345678'"), "unsafe")

    def test_password(self):
        self.assertEqual(safemode.risk_level("password: 'secretpass123'"), "unsafe")

    def test_token(self):
        self.assertEqual(safemode.risk_level("token = 'abcd1234abcd1234'"), "unsafe")

    def test_private_key(self):
        self.assertEqual(safemode.risk_level("private_key = 'ABCD1234ABCD1234'"), "unsafe")

    def test_stack_trace(self):
        self.assertEqual(
            safemode.risk_level('Traceback (most recent call last):\n  File "x.py", line 10'),
            "unsafe",
        )

    def test_error_caution(self):
        self.assertEqual(safemode.risk_level("error: something failed"), "caution")

    def test_benign_safe(self):
        self.assertEqual(
            safemode.risk_level("def add(a, b):\n    return a + b"), "safe"
        )

    def test_should_compress(self):
        self.assertFalse(safemode.should_compress("api_key = 'ABCDEFGH12345678'"))
        self.assertTrue(safemode.should_compress("def add(a,b):\n return a+b"))

    def test_multiline_secret(self):
        txt = "config:\n  secret = 'supersecretvalue123'\n  other = 1"
        self.assertEqual(safemode.risk_level(txt), "unsafe")


if __name__ == "__main__":
    unittest.main()
