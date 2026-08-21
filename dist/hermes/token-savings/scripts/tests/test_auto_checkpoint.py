"""Auto checkpoint (v10) - heuristic open-work extraction."""
import unittest

from toks import checkpoint


class TestAutoCheckpoint(unittest.TestCase):
    def test_extracts_next_steps(self):
        s = checkpoint.auto_state("We fixed the parser.\nTODO: add tests\nnext: run bench\n")
        self.assertTrue(any("TODO: add tests" in n for n in s["Next steps"]))
        self.assertTrue(any("run bench" in n for n in s["Next steps"]))

    def test_extracts_decisions(self):
        s = checkpoint.auto_state("decided: use stdlib only\nnext: ship it\n")
        self.assertTrue(any("use stdlib only" in d for d in s["Decisions"]))

    def test_active_task_first_substantive_line(self):
        s = checkpoint.auto_state("# meeting\nImplement the input gate and verify it\nnext: run tests\n")
        self.assertIn("input gate", s["Active task"])

    def test_empty(self):
        s = checkpoint.auto_state("")
        self.assertEqual(s["Active task"], "(none)")

    def test_emits_block(self):
        out = checkpoint.emit_checkpoint(checkpoint.auto_state("TODO: verify\n"))
        self.assertIn("Active task", out)


if __name__ == "__main__":
    unittest.main()