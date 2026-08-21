"""Surface-first extraction (v8) - read-me-first API surface."""
import unittest

from toks import surface


PY = "import os\n\ndef hello(name):\n    return name\n\nclass Foo:\n    def bar(self):\n        pass\n"


class TestSurface(unittest.TestCase):
    def test_py_symbols_with_line_numbers(self):
        s = surface.surface(PY, lang="py")
        self.assertIn("def hello(name)", s)
        self.assertIn("class Foo", s)
        self.assertIn("import os", s)
        self.assertIn("L3", s)          # def is at line 3
        self.assertIn("L7", s)          # class is at line 7

    def test_py_data_module_assignments(self):
        s = surface.surface("BIG = {'a': 1}\nNAME = 'x'\n", lang="py")
        self.assertIn("BIG = dict", s)
        self.assertIn("NAME =", s)

    def test_py_bad_syntax_fallback(self):
        s = surface.surface("def broken(:\n", lang="py")
        self.assertIn("parse error", s)

    def test_json_keys_and_types(self):
        s = surface.surface('{"a": 1, "b": {"c": [1, 2]}}', lang="json")
        self.assertIn("a : int", s)
        self.assertIn("b : dict", s)
        self.assertIn("c[0]", s)

    def test_json_invalid(self):
        s = surface.surface("{nope", lang="json")
        self.assertIn("invalid JSON", s)

    def test_md_headings(self):
        s = surface.surface("# Title\n\n## Section\n\nbody", lang="md")
        self.assertIn("# Title", s)
        self.assertIn("## Section", s)

    def test_conf_keys(self):
        s = surface.surface("[db]\nhost = localhost\nport = 5432", lang="conf")
        self.assertIn("[db]", s)
        self.assertIn("host = localhost", s)

    def test_detect_by_extension(self):
        self.assertEqual(surface.detect_lang("x", path="a.py"), "py")
        self.assertEqual(surface.detect_lang("x", path="a.json"), "json")
        self.assertEqual(surface.detect_lang("x", path="a.md"), "md")
        self.assertEqual(surface.detect_lang("x", path="a.toml"), "conf")

    def test_detect_by_sniffing(self):
        self.assertEqual(surface.detect_lang('{"a":1}'), "json")
        self.assertEqual(surface.detect_lang("# Heading"), "md")
        self.assertEqual(surface.detect_lang("def x():\n    pass\n"), "py")


if __name__ == "__main__":
    unittest.main()