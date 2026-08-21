"""Markdown-first normalization (USE-8): HTML -> clean Markdown, meaning kept."""
import unittest

from toks import mdnorm


class TestHTMLToMarkdown(unittest.TestCase):
    def test_strips_chrome_and_scripts(self):
        html = (
            "<html><head><style>x{}</style></head><body>"
            "<nav>menu</nav><h1>Title</h1><p>Hello</p>"
            "<script>evil()</script><footer>foot</footer></body></html>"
        )
        md = mdnorm.html_to_markdown(html)
        self.assertIn("# Title", md)
        self.assertIn("Hello", md)
        self.assertNotIn("menu", md)
        self.assertNotIn("evil", md)
        self.assertNotIn("foot", md)
        self.assertNotIn("x{}", md)

    def test_emphasis_and_links(self):
        md = mdnorm.html_to_markdown(
            '<p>Hello <b>world</b> and <em>you</em>. '
            '<a href="https://x.io">link</a></p>'
        )
        self.assertIn("**world**", md)
        self.assertIn("*you*", md)
        self.assertIn("[link](https://x.io)", md)

    def test_lists(self):
        md = mdnorm.html_to_markdown(
            "<ul><li>one</li><li>two</li></ul>"
            "<ol><li>first</li><li>second</li></ol>"
        )
        self.assertIn("- one", md)
        self.assertIn("- two", md)
        self.assertIn("1. first", md)
        self.assertIn("2. second", md)

    def test_code_block_and_inline_code(self):
        md = mdnorm.html_to_markdown(
            "<p>use <code>x = 1</code> now</p><pre>def f():\n    pass\n</pre>"
        )
        self.assertIn("`x = 1`", md)
        self.assertIn("```", md)
        self.assertIn("def f():", md)

    def test_table(self):
        md = mdnorm.html_to_markdown(
            "<table><tr><th>a</th><th>b</th></tr>"
            "<tr><td>1</td><td>2</td></tr></table>"
        )
        self.assertIn("| a | b |", md)
        self.assertIn("| 1 | 2 |", md)
        self.assertIn("---", md)

    def test_heading_and_paragraph_on_separate_lines(self):
        md = mdnorm.html_to_markdown(
            "<h1>Title</h1><p>Hello <b>world</b></p>"
        )
        self.assertIn("# Title\nHello **world**", md)

    def test_blockquote(self):
        md = mdnorm.html_to_markdown("<blockquote>quote text</blockquote>")
        self.assertIn("> quote text", md)

    def test_hr_and_img(self):
        md = mdnorm.html_to_markdown(
            '<hr><img alt="pic" src="a.png">'
        )
        self.assertIn("---", md)
        self.assertIn("![pic](a.png)", md)

    def test_protected_zone_survives(self):
        html = "<p>keep this: [[KEEP]]tok_abc123_important[[/KEEP]] intact</p>"
        md = mdnorm.html_to_markdown(html)
        self.assertIn("[[KEEP]]tok_abc123_important[[/KEEP]]", md)
        self.assertIn("keep this:", md)


class TestNormalizeMarkdown(unittest.TestCase):
    def test_collapses_blank_lines(self):
        md = mdnorm.normalize_markdown("a\n\n\n\n\nb\n\n\nc")
        self.assertEqual(md, "a\n\nb\n\nc")

    def test_trims_trailing_whitespace(self):
        md = mdnorm.normalize_markdown("line1   \nline2\t\n")
        self.assertNotIn("line1   ", md)
        self.assertEqual(md, "line1\nline2")

    def test_code_block_interior_untouched(self):
        md = mdnorm.normalize_markdown("before\n```\n\n\n\ncode\n```\nafter")
        self.assertIn("\n\n\n\ncode", md)


class TestEstimateSavings(unittest.TestCase):
    def test_reduction_pct(self):
        s = mdnorm.estimate_savings("x" * 100, "x" * 25)
        self.assertEqual(s["reduced_chars"], 75)
        self.assertEqual(s["pct"], 75.0)

    def test_zero_before(self):
        s = mdnorm.estimate_savings("", "abc")
        self.assertEqual(s["pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
