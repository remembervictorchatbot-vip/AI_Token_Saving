"""Semantic chunking of source files into reviewable units.

Python files are parsed with the stdlib `ast` module so chunks align to real
functions / methods / classes. VBA files are split on `Sub`/`Function`/
`Property ... End` boundaries. Other languages fall back to a brace-based
heuristic. The point: split by *structure*, not by line count.
"""

import ast
import os
import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    id: str
    module: str          # dotted module path, e.g. "app.service"
    file: str            # relative path
    kind: str            # function | method | class
    name: str            # simple name
    qualified: str       # module.name or module.Class.method
    start_line: int
    end_line: int
    source: str
    calls: list = field(default_factory=list)  # call targets seen in this chunk


# ---- VBA support --------------------------------------------------------
VBA_EXTS = {".vba", ".bas", ".cls", ".frm"}
VBA_PROC_RE = re.compile(
    r'^\s*(?:Public\s+|Private\s+|Friend\s+|Static\s+)*'
    r'(Sub|Function|Property\s+(?:Get|Let|Set))\s+([A-Za-z_]\w*)',
    re.IGNORECASE,
)
VBA_END_RE = re.compile(r'^\s*End\s+(Sub|Function|Property)\b', re.IGNORECASE)


def looks_like_vba(src):
    """Cheap sniff: does this text look like a VBA module?"""
    if re.search(r'\b(?:Sub|Function)\s+[A-Za-z_]\w*\s*\(', src) and \
       re.search(r'End\s+(?:Sub|Function)', src):
        return True
    return False


def _extract_vba_calls(src):
    """Heuristic: identifiers invoked like `Name(`. Excludes VBA keywords."""
    calls = set()
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(', src):
        calls.add(m.group(1))
    return sorted(calls)


def chunk_vba(source, rel_path, module):
    """Split a VBA module into procedures (Sub/Function/Property ... End)."""
    chunks = []
    lines = source.splitlines()
    n = len(lines)
    pending = None  # (kind, name, start_idx)
    i = 0
    while i < n:
        line = lines[i]
        m = VBA_PROC_RE.match(line)
        if m and pending is None:
            kw = m.group(1).lower()
            kind = "function" if kw == "function" else "method"
            pending = (kind, m.group(2), i)
            i += 1
            continue
        if pending is not None:
            if VBA_END_RE.match(line):
                start = pending[2]
                src = "\n".join(lines[start:i + 1])
                q = f"{module}.{pending[1]}"
                chunks.append(Chunk(
                    id=f"{module}:{q}",
                    module=module, file=rel_path,
                    kind=pending[0], name=pending[1], qualified=q,
                    start_line=start + 1, end_line=i + 1,
                    source=src,
                    calls=_extract_vba_calls(src),
                ))
                pending = None
            i += 1
            continue
        i += 1
    if not chunks:
        chunks.append(Chunk(
            id=f"{module}:all", module=module, file=rel_path, kind="function",
            name="module", qualified=module, start_line=1,
            end_line=max(1, n), source=source,
        ))
    return chunks


def _attr_to_str(node):
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts)) if parts else ""


def _extract_calls(func_node):
    out = []
    for n in ast.walk(func_node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.append(f.id)
            elif isinstance(f, ast.Attribute):
                s = _attr_to_str(f)
                if s:
                    out.append(s)
    return out


def chunk_python(source, rel_path, module):
    chunks = []
    lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=rel_path)
    except SyntaxError:
        return chunks

    def snippet(node):
        end = getattr(node, "end_lineno", node.lineno)
        return "\n".join(lines[node.lineno - 1:end])

    class_stack = []

    def visit(node):
        if isinstance(node, ast.ClassDef):
            class_stack.append(node.name)
            q = ".".join([module] + class_stack)
            chunks.append(Chunk(
                id=f"{module}:{q}",
                module=module, file=rel_path, kind="class",
                name=node.name, qualified=q,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                source=snippet(node),
            ))
            for child in node.body:
                visit(child)
            class_stack.pop()
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            q = ".".join([module] + class_stack + [node.name])
            chunks.append(Chunk(
                id=f"{module}:{q}",
                module=module, file=rel_path,
                kind="method" if class_stack else "function",
                name=node.name, qualified=q,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                source=snippet(node),
                calls=_extract_calls(node),
            ))

    for top in tree.body:
        visit(top)
    return chunks


def chunk_generic(source, rel_path, module):
    """Heuristic brace-based chunker for non-Python, non-VBA languages."""
    chunks = []
    lines = source.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if "{" in line:
            depth = 0
            started = False
            j = i
            while j < n:
                for ch in lines[j]:
                    if ch == "{":
                        depth += 1
                        started = True
                    elif ch == "}":
                        depth -= 1
                if started and depth == 0:
                    break
                j += 1
            end = j if j < n else n - 1
            chunks.append(Chunk(
                id=f"{module}:{i + 1}",
                module=module, file=rel_path, kind="function",
                name=f"block@{i + 1}", qualified=f"{module}@{i + 1}",
                start_line=i + 1, end_line=end + 1,
                source="\n".join(lines[i:end + 1]),
            ))
            i = end + 1
        else:
            i += 1
    if not chunks:
        chunks.append(Chunk(
            id=f"{module}:all", module=module, file=rel_path, kind="function",
            name="module", qualified=module, start_line=1,
            end_line=max(1, n), source=source,
        ))
    return chunks


def chunk_file(source, rel_path, module):
    """Dispatch to the right chunker by extension (with a VBA sniff for .txt)."""
    ext = os.path.splitext(rel_path)[1].lower()
    if ext == ".py":
        return chunk_python(source, rel_path, module)
    if ext in VBA_EXTS or (ext == ".txt" and looks_like_vba(source)):
        return chunk_vba(source, rel_path, module)
    return chunk_generic(source, rel_path, module)
