"""Markdown-first normalization for web / RAG ingestion (USE-8).

Goal: turn raw HTML (or messy Markdown) into clean Markdown that keeps the
*meaning* but drops the markup overhead and boilerplate that waste tokens
before anything reaches the model. Pure stdlib, provider-agnostic.

What it DROPS (by design):
- <script>, <style>, <head>, <noscript>, <template>, <svg>, <iframe>
- navigation / chrome: <nav>, <header>, <footer>, <aside>, <form>
- HTML entity noise, redundant blank lines, trailing whitespace

What it KEEPS:
- headings, paragraphs, lists, links, inline code, code blocks, tables,
  blockquotes, emphasis, images (as alt+src), horizontal rules
- protected zones [[KEEP]]...[[/KEEP]] pass through untouched

Lossy-but-safe: we never delete the user's literal content inside [[KEEP]].
"""
from html.parser import HTMLParser
import re

PROTECT_OPEN = "[[KEEP]]"
PROTECT_CLOSE = "[[/KEEP]]"

# Tags whose entire subtree is discarded (chrome / non-content).
SKIP_TAGS = {
    "script", "style", "head", "noscript", "template", "svg",
    "iframe", "nav", "header", "footer", "aside", "form", "meta", "link",
}


class _HTMLToMarkdown(HTMLParser):
    """HTML -> Markdown via a prefix + inline-buffer line model.

    Block tags set a line PREFIX ("# ", "- ", "> "); inline content (data,
    emphasis, links, code) accumulates in the buffer; the line is emitted on
    block close. This keeps heading/list/quote markers on the same line as
    their content.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0          # >0 while inside a skipped tag subtree
        self.list_stack = []         # (ordered_bool, item_count)
        self.in_pre = False
        self.prefix = ""             # current line prefix ("# ", "- ", "> ")
        self.buf = ""                # inline accumulator for current line
        self._link = ""
        self.in_td = False
        self.td_buffer = []
        self.table_rows = []

    # -- helpers ---------------------------------------------------------
    def _end_line(self):
        if self.prefix or self.buf:
            self.out.append(self.prefix + self.buf)
        self.prefix = ""
        self.buf = ""

    # -- tag handling ----------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            self.skip_depth += 1   # any nested tag inside a skipped subtree deepens it
            return
        if tag in SKIP_TAGS:
            self.skip_depth = 1
            return
        a = dict(attrs)
        if tag == "br":
            self._end_line()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.prefix = "#" * int(tag[1]) + " "
        elif tag == "pre":
            self._end_line()
            self.in_pre = True
            self.out.append("```")
        elif tag == "code" and not self.in_pre:
            self.buf += "`"
        elif tag in ("strong", "b"):
            self.buf += "**"
        elif tag in ("em", "i"):
            self.buf += "*"
        elif tag == "a":
            self.buf += "["
            self._link = a.get("href", "")
        elif tag == "ul":
            self.list_stack.append((False, 0))
        elif tag == "ol":
            self.list_stack.append((True, 0))
        elif tag == "li":
            ordered, n = self.list_stack[-1] if self.list_stack else (False, 0)
            n += 1
            if self.list_stack:
                self.list_stack[-1] = (ordered, n)
            self.prefix = f"{n}. " if ordered else "- "
        elif tag == "blockquote":
            self.prefix = "> " + self.prefix
        elif tag == "hr":
            self._end_line()
            self.out.append("---")
        elif tag == "img":
            alt, src = a.get("alt", ""), a.get("src", "")
            if alt or src:
                self.buf += f"![{alt}]({src})"
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr":
            self.td_buffer = []
        elif tag in ("td", "th"):
            self.in_td = True
            self.buf = ""

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag == "pre":
            self.in_pre = False
            self.out.append("```")
        elif tag == "code" and not self.in_pre:
            self.buf += "`"
        elif tag in ("strong", "b"):
            self.buf += "**"
        elif tag in ("em", "i"):
            self.buf += "*"
        elif tag == "a":
            self.buf += f"]({getattr(self, '_link', '')})"
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self._end_line()
        elif tag == "li":
            self._end_line()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "blockquote"):
            self._end_line()
        elif tag == "tr":
            self.table_rows.append("| " + " | ".join(self.td_buffer) + " |")
        elif tag in ("td", "th"):
            self.in_td = False
            self.td_buffer.append(self.buf.strip())
            self.buf = ""
        elif tag == "table":
            self._end_line()
            if self.table_rows:
                sep = re.sub(r"[^|]", "-", self.table_rows[0]).replace("|", "-")
                self.out.append(self.table_rows[0])
                self.out.append(sep)
                self.out.extend(self.table_rows[1:])

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.in_pre:
            self.out.append(data)
        else:
            self.buf += data

    def finish(self):
        """Flush any pending inline content (e.g. a trailing self-closing img)."""
        self._end_line()


def html_to_markdown(html: str) -> str:
    """Convert raw HTML to clean Markdown, preserving content meaning."""
    protected = _extract_protected(html)
    # Replace protected zones with stable placeholders so the parser
    # cannot mangle their contents.
    ph = {}
    for i, p in enumerate(protected):
        key = f"\x00KEEP{i}\x00"
        ph[key] = p
        html = html.replace(PROTECT_OPEN + p + PROTECT_CLOSE, key, 1)

    parser = _HTMLToMarkdown()
    parser.feed(html)
    parser.close()
    parser.finish()
    # Normalize BEFORE restoring protected zones so the normalizer can never
    # alter the user's literal [[KEEP]] content.
    md = normalize_markdown("\n".join(parser.out))
    for key, val in ph.items():
        md = md.replace(key, PROTECT_OPEN + val + PROTECT_CLOSE)
    return md


def normalize_markdown(md: str) -> str:
    """Clean already-Markdown text: collapse 3+ blank lines to one, trim trailing
    whitespace, and strip leading/trailing whitespace blocks."""
    # Protect code blocks first so we don't touch their interior.
    blocks = {}

    def _stash(m):
        k = f"\x00CODE{len(blocks)}\x00"
        blocks[k] = m.group(0)
        return k

    md = re.sub(r"```.*?```", _stash, md, flags=re.DOTALL)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = "\n".join(line.rstrip() for line in md.splitlines())
    md = md.strip()
    for k, v in blocks.items():
        md = md.replace(k, v)
    return md


def _extract_protected(text: str) -> list:
    return re.findall(
        re.escape(PROTECT_OPEN) + r"(.*?)" + re.escape(PROTECT_CLOSE), text, re.DOTALL
    )


def estimate_savings(before: str, after: str) -> dict:
    """Provider-agnostic char-based reduction (keeps skill free of tiktoken dep)."""
    b, a = len(before), len(after)
    red = max(0, b - a)
    pct = round(100.0 * red / b, 1) if b else 0.0
    return {"before_chars": b, "after_chars": a, "reduced_chars": red, "pct": pct}
