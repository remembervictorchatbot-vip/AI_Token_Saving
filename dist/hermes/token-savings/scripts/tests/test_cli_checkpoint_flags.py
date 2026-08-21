"""End-to-end check that checkpoint CLI exposes --open-questions/--lessons (fixes D2)."""
import os
import subprocess
import sys
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCliCheckpointFlags(unittest.TestCase):
    def test_flags_emit(self):
        out = subprocess.run(
            [sys.executable, "-m", "toks.cli", "checkpoint", "--emit",
             "--active-task", "T", "--open-questions", "q1|q2", "--lessons", "l1"],
            cwd=SCRIPTS, capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("Open questions", out.stdout)
        self.assertIn("Lessons to carry", out.stdout)
        self.assertIn("q1", out.stdout)
        self.assertIn("q2", out.stdout)
        self.assertIn("l1", out.stdout)
