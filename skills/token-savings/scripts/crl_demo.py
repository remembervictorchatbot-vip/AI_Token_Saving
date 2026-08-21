"""Demo: measure token savings of targeted review vs whole-repo review.

Run:  python demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from crl.index import Index
from crl.retrieve import Retriever, assemble
from crl.tokens import estimate

ROOT = os.path.join(os.path.dirname(__file__), "sample_repo")


def row(label, chunks):
    ctx = assemble(chunks)
    return label, len(chunks), estimate(ctx), ctx


def scenario(idx, retr, changed):
    print("=" * 72)
    print(f"SCENARIO: changed files = {changed}")
    print("=" * 72)

    whole = idx.chunks
    mod = retr.retrieve(changed, mode="module")
    fn = retr.retrieve(changed, mode="function")

    w_label, w_n, w_tok, _ = row("whole-repo", whole)
    m_label, m_n, m_tok, _ = row("module-mode", mod)
    f_label, f_n, f_tok, _ = row("function-mode", fn)

    whole_tok = w_tok
    print(f"{'strategy':<14}{'chunks':>8}{'tokens':>10}{'input saved':>14}")
    print(f"{w_label:<14}{w_n:>8}{w_tok:>10}{'-':>14}")
    print(f"{m_label:<14}{m_n:>8}{m_tok:>10}{100*(1-m_tok/whole_tok):>12.1f}%")
    print(f"{f_label:<14}{f_n:>8}{f_tok:>10}{100*(1-f_tok/whole_tok):>12.1f}%")

    mods = sorted({c.module for c in mod})
    fnmods = sorted({c.module for c in fn})
    print(f"\nmodule-mode modules ({len(mods)}): {mods}")
    print(f"function-mode modules ({len(fnmods)}): {fnmods}")
    print()


def main():
    idx = Index(ROOT)
    idx.build()
    retr = Retriever(idx)
    print(f"Index: {len(idx.chunks)} chunks, {len(idx.by_module)} modules\n")

    # Leaf change: nothing depends on main.py, so dependents are empty and
    # only the forward import closure (service, utils) is pulled in.
    scenario(idx, retr, ["app/main.py"])

    # Widely-depended change: everything imports utils.py, so a naive
    # dependents expansion drags in the big db.py. Function-mode still trims
    # db.py down to only the symbols utils actually touches.
    scenario(idx, retr, ["app/utils.py"])


if __name__ == "__main__":
    main()
