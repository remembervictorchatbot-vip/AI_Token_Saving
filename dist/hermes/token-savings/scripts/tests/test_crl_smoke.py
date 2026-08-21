"""Smoke test for the consolidated crl code-review engine (folded into token-savings)."""
import importlib
import os
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCrlSmoke(unittest.TestCase):
    def test_crl_package_imports(self):
        mod = importlib.import_module("crl.cli")
        self.assertIsNotNone(mod)

    def test_crl_demo_exists(self):
        self.assertTrue(os.path.exists(os.path.join(SCRIPTS, "crl_demo.py")))

    def test_sample_repo_exists(self):
        self.assertTrue(os.path.isdir(os.path.join(SCRIPTS, "sample_repo")))

    def test_crl_cli_has_review(self):
        import crl.cli as cli

        self.assertTrue(hasattr(cli, "main") or hasattr(cli, "run") or hasattr(cli, "review"))


if __name__ == "__main__":
    unittest.main()
