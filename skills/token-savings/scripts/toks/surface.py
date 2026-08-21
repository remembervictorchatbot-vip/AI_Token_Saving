"""Surface-first extraction - "read me first", not a compressor (new, v8).

For any file >~150 lines, extract the API SURFACE first - one line per
symbol/heading/key with line numbers - and read the full content only when a
surface line proves relevant. Input-side counterpart to astrip: astrip
compresses re-reads; surface avoids full reads in the first place.
Pure stdlib: ast for Python, regex for json/md/conf. Deterministic.
"""
import ast
import json
import re


def _py_surface(text: str) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        skel = [ln for ln in text.splitlines()
                if re.match(r"^\s*(def |class |import |from )", ln)]
        return "[surface: parse error - regex fallback]\n" + "\n".join(skel)
    out = []
    # top-level assignments are the surface of data/config modules
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
                name = getattr(t, "id", None) or getattr(t, "attr", None)
                if name is None:
                    continue
                val = n.value
                if isinstance(val, ast.Constant):
                    v = repr(val.value)[:40]
                elif isinstance(val, ast.Dict):
                    v = "dict"
                elif isinstance(val, (ast.List, ast.Tuple)):
                    v = type(val).__name__
                else:
                    v = type(val).__name__
                out.append((n.lineno, f"{name} = {v}"))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in n.args.args]
            sig = n.name + "(" + ", ".join(args) + ")"
            kind = "async def" if isinstance(n, ast.AsyncFunctionDef) else "def"
            out.append((n.lineno, f"{kind} {sig}"))
        elif isinstance(n, ast.ClassDef):
            bases = ", ".join(ast.unparse(b) for b in n.bases)
            line = f"class {n.name}({bases})" if bases else f"class {n.name}"
            out.append((n.lineno, line))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            try:
                out.append((n.lineno, ast.unparse(n)))
            except Exception:
                pass
    seen, lines = set(), []
    for ln, t in sorted(set(out)):
        if (ln, t) not in seen:
            seen.add((ln, t))
            lines.append(f"L{ln}  {t}")
    return f"[surface: {len(lines)} symbols]\n" + "\n".join(lines)


def _json_surface(text: str, max_depth: int = 3) -> str:
    try:
        data = json.loads(text)
    except Exception as e:
        return f"[surface: invalid JSON - {e}]"
    out = []

    def walk(v, path, depth):
        if depth > max_depth:
            return
        if isinstance(v, dict):
            for k, val in v.items():
                p = f"{path}.{k}" if path else k
                out.append(f"L1  {p} : {type(val).__name__}")
                walk(val, p, depth + 1)
        elif isinstance(v, list) and v:
            out.append(f"L1  {path}[0] : {type(v[0]).__name__} (len {len(v)})")
            walk(v[0], f"{path}[0]", depth + 1)

    walk(data, "", 0)
    return "[surface: json keys]\n" + "\n".join(out)


def _md_surface(text: str) -> str:
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        s = ln.strip()
        if re.match(r"^#{1,6}\s", s) or re.match(r"^```", s):
            out.append(f"L{i}  {s}")
    return "[surface: markdown headings]\n" + "\n".join(out)


def _conf_surface(text: str) -> str:
    out = []
    for i, ln in enumerate(text.splitlines(), 1):
        s = ln.strip()
        if re.match(r"^\[.*\]$", s) or re.match(r"^[A-Za-z_][\w.]*\s*=", s):
            out.append(f"L{i}  {s}")
    return "[surface: config keys]\n" + "\n".join(out)


def detect_lang(text: str, path: str = "") -> str:
    """Auto-detect surface language: by extension, then content sniffing."""
    if path:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext in ("py", "pyw"):
            return "py"
        if ext == "json":
            return "json"
        if ext in ("md", "markdown", "rst"):
            return "md"
        if ext in ("ini", "cfg", "conf", "toml", "env"):
            return "conf"
    head = text.lstrip()[:64]
    if head.startswith("{") or head.startswith("["):
        return "json"
    if head.startswith("#") or head.startswith("---"):
        return "md"
    if re.search(r"^\[[^]]+\]$", text, re.M):
        return "conf"
    return "py"


def surface(text: str, lang: str = "auto", path: str = "") -> str:
    """Return the API surface of `text` - one line per symbol, with line numbers."""
    if lang == "auto":
        lang = detect_lang(text, path)
    if lang == "json":
        return _json_surface(text)
    if lang == "md":
        return _md_surface(text)
    if lang == "conf":
        return _conf_surface(text)
    return _py_surface(text)