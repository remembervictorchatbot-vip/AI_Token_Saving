"""Portable skill-dir resolution + launcher shim (v7)."""
import os
import subprocess
import tempfile
import unittest

from toks import boot

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(boot.__file__))))
SHIM = os.path.join(ROOT, "bin", "toks")  # skill root's bin/toks


class TestBoot(unittest.TestCase):
    def test_autodetect_finds_scripts(self):
        d = boot.skill_dir()
        self.assertIsNotNone(d)
        self.assertTrue(os.path.isdir(os.path.join(d, "scripts", "toks")))

    def test_scripts_dir(self):
        s = boot.scripts_dir()
        self.assertTrue(os.path.isfile(os.path.join(s, "toks", "cli.py")))

    def test_env_override_wins(self):
        old = os.environ.get("TOKS_SKILL_DIR")
        os.environ["TOKS_SKILL_DIR"] = ROOT
        try:
            self.assertEqual(boot.skill_dir(), ROOT)
        finally:
            if old is None:
                del os.environ["TOKS_SKILL_DIR"]
            else:
                os.environ["TOKS_SKILL_DIR"] = old

    def test_invalid_env_falls_back(self):
        old = os.environ.get("TOKS_SKILL_DIR")
        os.environ["TOKS_SKILL_DIR"] = "/nonexistent"
        try:
            d = boot.skill_dir()
            self.assertIsNotNone(d)          # fell through to autodetect
            self.assertTrue(os.path.isdir(os.path.join(d, "scripts", "toks")))
        finally:
            if old is None:
                del os.environ["TOKS_SKILL_DIR"]
            else:
                os.environ["TOKS_SKILL_DIR"] = old


class TestShim(unittest.TestCase):
    def test_shim_runs_from_any_cwd(self):
        # On Windows, test the .bat launcher; on POSIX, test the shell script.
        shim = os.path.join(ROOT, "bin", "toks.bat") if os.name == "nt" else SHIM
        if not os.path.isfile(shim):
            self.skipTest(f"launcher not found: {shim}")
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run(
                [shim, "--help"],
                cwd=tmp,
                capture_output=True, text=True,
            )
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("usage", out.stdout.lower())

    def test_shim_script_exists_and_executable(self):
        self.assertTrue(os.path.isfile(SHIM))
        if os.name != "nt":  # exec bit matters on unix
            self.assertTrue(os.access(SHIM, os.X_OK))


if __name__ == "__main__":
    unittest.main()
