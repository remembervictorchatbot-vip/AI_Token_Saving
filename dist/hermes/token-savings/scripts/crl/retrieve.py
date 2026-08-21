"""Diff-aware retrieval: load only the closure of code a task touches.

Two modes:
  - "module":   whole relevant modules (changed + dependents + depth-limited
                imports + tests). Safe, moderate savings.
  - "function": changed modules in full (you need file context to edit), but
                dependent modules trimmed to only the symbols actually used by
                the changed code. Aggressive, max savings, slightly riskier.
"""

from .index import Index


def assemble(chunks):
    blocks = []
    for c in chunks:
        blocks.append(
            f"# {c.file}:{c.start_line}-{c.end_line} [{c.kind}] {c.qualified}\n{c.source}\n"
        )
    return "\n".join(blocks)


class Retriever:
    def __init__(self, index: Index):
        self.index = index

    def relevant_modules(self, changed_modules, import_depth=1):
        seen = set(changed_modules)
        # Reverse edge: modules that import a changed module (its dependents).
        stack = list(changed_modules)
        while stack:
            m = stack.pop()
            for dep in self.index.dependents.get(m, ()):
                if dep not in seen:
                    seen.add(dep)
                    stack.append(dep)
        # Forward edge: depth-limited imports (shared/interface files).
        frontier = list(changed_modules)
        for _ in range(import_depth):
            nxt = []
            for m in frontier:
                for imp in self.index.imports.get(m, ()):
                    if imp not in seen:
                        seen.add(imp)
                        nxt.append(imp)
            frontier = nxt
        return seen

    def retrieve(self, changed_files, mode="module", import_depth=1):
        idx = self.index
        changed_modules = [idx.module_of(f) for f in changed_files]
        rel_modules = self.relevant_modules(changed_modules, import_depth)

        # Tests that exercise anything in the relevant set.
        test_modules = {tm for tm in idx.tests if idx.imports.get(tm, ()) & rel_modules}

        if mode == "module":
            selected = []
            for m in rel_modules | test_modules:
                selected.extend(idx.by_module.get(m, []))
            return selected

        # ---- function-level surgical mode ----
        changed_simple = set()
        called_simple = set()
        for m in changed_modules:
            for c in idx.by_module.get(m, []):
                if c.kind in ("function", "method"):
                    changed_simple.add(c.name)
                for call in c.calls:
                    called_simple.add(call.split(".")[-1])

        selected = []
        for m in rel_modules:
            if m in changed_modules:
                # Keep full context for the files actually being edited.
                selected.extend(idx.by_module.get(m, []))
                continue
            for c in idx.by_module.get(m, []):
                if c.kind == "class":
                    continue  # skip class scaffolding in dependents unless a method matches
                if c.name in changed_simple or c.name in called_simple:
                    selected.append(c)
                    continue
                if any(call.split(".")[-1] in changed_simple for call in c.calls):
                    selected.append(c)
        for tm in test_modules:
            selected.extend(idx.by_module.get(tm, []))
        return selected

    def retrieve_procedure(self, changed_file, proc_name):
        """Surgical: return only the named procedure from the changed file."""
        idx = self.index
        mod = idx.module_of(changed_file)
        for c in idx.by_module.get(mod, []):
            if c.name == proc_name and c.kind in ("function", "method"):
                return [c]
        return []
