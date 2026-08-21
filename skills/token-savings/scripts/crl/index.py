"""Inverted index over the codebase: chunks + import graph + reverse dependents.

Built ONCE per repo (incrementally maintainable). This is the missing piece in
the naive "split and guess relevance" idea: the index makes relevance
*computable* instead of guessed.
"""

import ast
import os
from .chunker import chunk_python, chunk_generic, chunk_vba, looks_like_vba, VBA_EXTS, Chunk

SUPPORTED = {".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".cs", ".rb", ".rs", ".vba", ".bas", ".cls", ".frm"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".crl", "dist", "build"}


class Index:
    def __init__(self, root):
        self.root = root
        self.chunks = []
        self.by_module = {}                 # module -> [Chunk]
        self.imports = {}                   # module -> set(module)
        self.dependents = {}                # module -> set(module that imports it)
        self.tests = set()                  # module names flagged as tests

    # ---- module naming -------------------------------------------------
    def module_of(self, rel_path):
        p = rel_path
        if p.startswith("./"):
            p = p[2:]
        base, _ = os.path.splitext(p)
        return base.replace(os.sep, ".")

    # ---- build ---------------------------------------------------------
    def build(self):
        for dirpath, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in SUPPORTED:
                    # .txt may be a VBA export; sniff it before skipping
                    if ext == ".txt":
                        try:
                            with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                                head = f.read(8000)
                        except Exception:
                            continue
                        if not looks_like_vba(head):
                            continue
                        lang = "vba"
                    else:
                        continue
                else:
                    lang = "vba" if ext in VBA_EXTS else ("py" if ext == ".py" else "generic")
                rel = os.path.relpath(os.path.join(dirpath, fn), self.root)
                self._index_file(rel, lang)
        self._build_dependents()
        self._classify_tests()

    def _index_file(self, rel, lang="generic"):
        mod = self.module_of(rel)
        path = os.path.join(self.root, rel)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        if lang == "py":
            chunks = chunk_python(src, rel, mod)
            imps = _extract_py_imports(src, mod)
        elif lang == "vba":
            chunks = chunk_vba(src, rel, mod)
            imps = set()
        else:
            chunks = chunk_generic(src, rel, mod)
            imps = set()
        self.imports[mod] = imps
        self.by_module[mod] = chunks
        self.chunks.extend(chunks)

    def _build_dependents(self):
        for mod, imps in self.imports.items():
            for imp in imps:
                self.dependents.setdefault(imp, set()).add(mod)

    def _classify_tests(self):
        for mod in self.by_module:
            if "test" in mod.split(".")[-1] or mod.split(".")[-1].startswith("test"):
                self.tests.add(mod)

    # ---- serialization (so indexing is a one-time cost) ---------------
    def to_dict(self):
        return {
            "root": self.root,
            "imports": {k: sorted(v) for k, v in self.imports.items()},
            "dependents": {k: sorted(v) for k, v in self.dependents.items()},
            "tests": sorted(self.tests),
            "chunks": [c.__dict__ for c in self.chunks],
            "by_module": {k: [c.id for c in v] for k, v in self.by_module.items()},
        }

    def from_dict(self, d):
        self.root = d["root"]
        self.imports = {k: set(v) for k, v in d["imports"].items()}
        self.dependents = {k: set(v) for k, v in d["dependents"].items()}
        self.tests = set(d["tests"])
        self.chunks = [Chunk(**c) for c in d["chunks"]]
        idmap = {c.id: c for c in self.chunks}
        self.by_module = {m: [idmap[i] for i in ids] for m, ids in d["by_module"].items()}


def _extract_py_imports(source, mod):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    pkg = mod.rsplit(".", 1)[0] if "." in mod else ""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name)
        elif isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if n.level:
                prefix = pkg
                for _ in range(n.level - 1):
                    prefix = prefix.rsplit(".", 1)[0] if "." in prefix else ""
                full_base = (prefix + "." + base) if base and prefix else (base or prefix)
            else:
                full_base = base
            if n.names and n.names[0].name != "*":
                # `from app import service` -> app.service (submodule edge)
                for a in n.names:
                    out.add((full_base + "." + a.name) if full_base else a.name)
            elif full_base:
                out.add(full_base)
    return out
