"""Output gate (v10) - self-enforcing O-1..O-6 checks before emit."""
import unittest

from toks import output


class TestOutputGate(unittest.TestCase):
    def test_short_reply_passes(self):
        g = output.gate_reply("Done - fixed the bug.\n", task_type="analysis")
        self.assertTrue(g["pass"])

    def test_budget_exceeded(self):
        g = output.gate_reply("verdict line\n" * 40, task_type="verdict")
        self.assertFalse(g["pass"])
        self.assertTrue(any("O-2" in i for i in g["issues"]))

    def test_filler_flagged_outside_chat(self):
        g = output.gate_reply("Result: ok\n\nI hope this helps!\n", task_type="report")
        self.assertFalse(g["pass"])
        self.assertTrue(any("O-5" in i for i in g["issues"]))

    def test_chat_politeness_allowed(self):
        g = output.gate_reply("Sure! I hope this helps.\n", task_type="chat_reply")
        self.assertTrue(g["pass"])

    def test_bad_json_flagged(self):
        g = output.gate_reply('{"a": 1,}', task_type="data_only")
        self.assertFalse(g["pass"])
        self.assertTrue(any("O-1" in i for i in g["issues"]))

    def test_unbalanced_fences_flagged(self):
        g = output.gate_reply("```py\nx = 1", task_type="code_snippet")
        self.assertFalse(g["pass"])
        self.assertTrue(any("O-6" in i for i in g["issues"]))


if __name__ == "__main__":
    unittest.main()