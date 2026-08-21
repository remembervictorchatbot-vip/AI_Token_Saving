"""Multi-surface compression primitives (JSON / bash / grep / skeleton)."""
import json
import unittest

from toks import compress


class TestCompress(unittest.TestCase):
    def test_compress_json_drops_nulls(self):
        out = compress.compress_json({"a": 1, "b": None, "c": None})
        self.assertNotIn("null", out)
        self.assertIn('"a":1', out)

    def test_compress_json_drops_debug(self):
        out = compress.compress_json(
            {"data": [1, 2], "debug": "trace", "log": "x", "stack": "y"}
        )
        self.assertNotIn("debug", out)
        self.assertNotIn("log", out)
        self.assertNotIn("stack", out)
        self.assertIn("data", out)

    def test_compress_json_keeps_nested(self):
        obj = {"x": {"y": 2, "z": None}, "debug": "d"}
        out = compress.compress_json(obj)
        self.assertIn('"y":2', out)
        self.assertNotIn("debug", out)

    def test_compress_json_keep_debug_flag(self):
        out = compress.compress_json({"debug": "x"}, drop_debug=False)
        self.assertIn("debug", out)

    def test_compress_json_values_intact(self):
        obj = {"name": "Ada", "id": 42, "ratio": 0.5}
        out = compress.compress_json(obj)
        self.assertIn("Ada", out)
        self.assertIn("42", out)

    def test_trim_bash_collapses_repeats(self):
        out = compress.trim_bash("\n".join(["same"] * 10), max_lines=40, collapse_repeats=3)
        self.assertIn("collapsed", out)
        self.assertNotIn("same", out)

    def test_trim_bash_keeps_few_repeats(self):
        out = compress.trim_bash("\n".join(["same"] * 2), collapse_repeats=3)
        self.assertIn("same", out)

    def test_trim_bash_strips_ansi(self):
        out = compress.trim_bash("\x1b[31mred text\x1b[0m")
        self.assertNotIn("\x1b", out)

    def test_trim_bash_truncates(self):
        out = compress.trim_bash(
            "\n".join(f"line{i}" for i in range(20)), max_lines=10
        )
        self.assertIn("omitted", out)

    def test_summarize_grep_within_top(self):
        lines = "\n".join(f"zzz{i}" for i in range(5))
        out = compress.summarize_grep(lines, top=10)
        self.assertEqual(out.count("zzz"), 5)

    def test_summarize_grep_over_top(self):
        lines = "\n".join(f"zzz{i}" for i in range(25))
        out = compress.summarize_grep(lines, top=10)
        self.assertIn("more matches", out)
        self.assertEqual(out.count("zzz"), 10)

    def test_skeleton_py(self):
        code = (
            "import os\nfrom sys import argv\n\ndef foo():\n    return 1\n\n"
            "class Bar:\n    pass\n# comment\n"
        )
        out = compress.skeleton(code, lang="py")
        self.assertIn("import os", out)
        self.assertIn("def foo", out)
        self.assertIn("class Bar", out)


if __name__ == "__main__":
    unittest.main()
