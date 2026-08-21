"""AST-based structure extraction + comment stripping (context compression 60-90%).

Drops function/class bodies (keep signatures + imports) for re-reads, optionally
strips comments. Full source stays recoverable via the dedup/expand cache (JIT
expansion). For non-Python, falls back to a regex skeleton.
"""
import ast
import re


def _regex_skeleton(code: str) -> str:
    out = []
    for ln in code.splitlines():
        s = ln.strip()
        if re.match(r"^(def |class |import |from |@|#)", s):
            out.append(ln)
    return "\n".join(out) + "\n[ skeleton fallback ]"


def _emit(node, drop_bodies: bool, indent: int) -> str:
    pad = "    " * indent
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        try:
            return pad + ast.unparse(node)
        except Exception:
            return None
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        try:
            line = f"{pad}def {node.name}({ast.unparse(node.args)}):"
        except Exception:
            line = f"{pad}def {node.name}(...):"
        if drop_bodies:
            return line + "  # [body omitted]"
        body = "\n".join(
            e for e in (_emit(n, drop_bodies, indent + 1) for n in node.body) if e
        )
        return line + ("\n" + body if body else "")
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(ast.unparse(b) for b in node.bases)
        line = f"{pad}class {node.name}({bases}):" if bases else f"{pad}class {node.name}:"
        if drop_bodies:
            return line + "  # [body omitted]"
        body = "\n".join(
            e for e in (_emit(n, drop_bodies, indent + 1) for n in node.body) if e
        )
        return line + ("\n" + body if body else "")
    if isinstance(node, ast.Assign):
        try:
            return pad + ast.unparse(node)
        except Exception:
            return None
    return None


def astrip(code: str, lang: str = "py", drop_bodies: bool = True,
           strip_comments: bool = True) -> str:
    """Return a compact structure-only view. Full code is recoverable via expand."""
    if lang != "py":
        return _regex_skeleton(code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return _regex_skeleton(code)
    parts = [_emit(n, drop_bodies, 0) for n in tree.body]
    parts = [p for p in parts if p]
    text = "\n".join(parts)
    if strip_comments:
        text = "\n".join(
            ln for ln in text.splitlines() if not ln.strip().startswith("#")
        )
    return text + "\n[ astrip: bodies/comments omitted; full via expand ]"
