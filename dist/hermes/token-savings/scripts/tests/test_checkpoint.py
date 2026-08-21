"""Auto-checkpoint before compaction - the loop's continuity backbone."""
import unittest

from toks import checkpoint


class TestCheckpoint(unittest.TestCase):
    def test_roundtrip(self):
        state = {
            "Active task": "Build X",
            "Decisions": ["d1", "d2"],
            "Modified files": ["a.py"],
            "Open questions": ["q1"],
            "Next steps": ["n1"],
            "Lessons to carry": ["l1"],
        }
        blk = checkpoint.emit_checkpoint(state)
        parsed = checkpoint.parse_checkpoint(blk)
        self.assertEqual(parsed.get("Active task"), "Build X")
        self.assertIn("d1", parsed.get("Decisions", ""))
        self.assertIn("l1", parsed.get("Lessons to carry", ""))

    def test_default_none(self):
        blk = checkpoint.emit_checkpoint({})
        parsed = checkpoint.parse_checkpoint(blk)
        self.assertEqual(parsed.get("Active task"), "(none)")

    def test_embedded_in_text(self):
        txt = (
            "some prose\n"
            + checkpoint.emit_checkpoint({"Active task": "Y"})
            + "\nafter"
        )
        parsed = checkpoint.parse_checkpoint(txt)
        self.assertEqual(parsed.get("Active task"), "Y")


if __name__ == "__main__":
    unittest.main()
