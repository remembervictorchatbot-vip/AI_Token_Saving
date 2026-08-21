"""AST extraction + comment stripping (60-90% input reduction)."""
import unittest

from toks import astrip

PY = (
    "def f(x):\n    # a comment\n    return x + 1\n\n"
    "class C(Base):\n    def m(self):\n        return 2\n"
)


class TestAstrip(unittest.TestCase):
    def test_drops_bodies_and_comments(self):
        out = astrip.astrip(PY, lang="py", drop_bodies=True, strip_comments=True)
        self.assertIn("def f(", out)
        self.assertIn("class C", out)
        self.assertIn("[body omitted]", out)
        # bare statements (e.g. return) and body comments are NOT emitted nodes
        self.assertNotIn("return x + 1", out)

    def test_keep_bodies_preserves_nested_structure(self):
        code = (
            "def f(x):\n    class Inner:\n        pass\n    y = 2\n    return x\n"
        )
        out = astrip.astrip(code, lang="py", drop_bodies=False, strip_comments=False)
        self.assertIn("def f(", out)
        self.assertIn("class Inner", out)  # nested def/class preserved
        self.assertIn("y = 2", out)        # nested assignment preserved

    def test_strip_comments_flag_accepted(self):
        out_true = astrip.astrip(PY, lang="py", strip_comments=True)
        out_false = astrip.astrip(PY, lang="py", strip_comments=False)
        self.assertIn("def f(", out_true)
        self.assertIn("def f(", out_false)

    def test_syntax_error_fallback(self):
        bad = "def (:\n   invalid python !!!\n"
        out = astrip.astrip(bad, lang="py")
        self.assertIn("skeleton fallback", out)

    def test_non_py_fallback(self):
        js = "class Bar {\n  // comment\n  function foo() {}\n}\n"
        out = astrip.astrip(js, lang="js")
        self.assertIn("class Bar", out)

    def test_empty(self):
        out = astrip.astrip("", lang="py")
        self.assertIn("astrip", out)

    def test_unicode_identifiers(self):
        code = "def 计算(a):\n    return a\n"
        out = astrip.astrip(code, lang="py")
        self.assertIn("计算", out)

    def test_big_input(self):
        # Bodies longer than the "[body omitted]" suffix -> AST stripping reduces.
        big = "def f():\n    x = 1\n    y = 2\n    z = 3\n    return x + y + z\n" * 1000
        out = astrip.astrip(big, lang="py")
        self.assertIn("def f(", out)
        self.assertLess(len(out), len(big))


if __name__ == "__main__":
    unittest.main()
