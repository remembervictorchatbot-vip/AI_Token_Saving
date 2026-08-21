"""CLI entry point for real repos.

  python -m crl.cli index  <repo>            # build + cache index
  python -m crl.cli review <repo> --changed app/utils.py --mode function
"""

import argparse
import json
import os
import sys

from .index import Index
from .retrieve import Retriever, assemble
from .tokens import estimate
from .preflight import run_preflight
from .analyze import summarize


def _fingerprint(repo, files):
    """(size, mtime) per indexed file — cheap staleness detection."""
    fp = {}
    for rel in sorted(files):
        p = os.path.join(repo, rel)
        try:
            st = os.stat(p)
            fp[rel] = [st.st_size, int(st.st_mtime)]
        except OSError:
            fp[rel] = None
    return fp


def cmd_index(args):
    idx = Index(args.repo)
    idx.build()
    data = idx.to_dict()
    data["fingerprint"] = _fingerprint(args.repo, {c.file for c in idx.chunks})
    out = os.path.join(args.repo, ".crl_index.json")
    with open(out, "w") as f:
        json.dump(data, f)
    print(f"Indexed {len(idx.chunks)} chunks across {len(idx.by_module)} modules -> {out}")


def load_index(repo, index_path):
    """Load the cached index, but REBUILD if the sources changed underneath it.

    A stale cache is the worst failure mode for a retrieval-based reviewer: it
    silently returns fewer chunks than exist, so procedures vanish from the
    review with no error. Verify before trusting.
    """
    idx = Index(repo)
    if index_path and os.path.exists(index_path):
        with open(index_path) as f:
            data = json.load(f)
        idx.from_dict(data)
        cached = data.get("fingerprint")
        current = _fingerprint(repo, {c.file for c in idx.chunks})
        if cached is None:
            print("WARNING: index has no fingerprint (built by an older version) "
                  "— rebuilding to guarantee coverage.", file=sys.stderr)
        elif cached != current:
            changed = sorted(
                k for k in set(cached) | set(current)
                if cached.get(k) != current.get(k)
            )
            print(f"WARNING: index is STALE for {changed} — rebuilding.", file=sys.stderr)
        else:
            return idx
        idx = Index(repo)
    idx.build()
    return idx


def cmd_review(args):
    idx = load_index(args.repo, args.index)
    retr = Retriever(idx)
    if args.procedure:
        if len(args.changed) != 1:
            print("ERROR: --procedure requires exactly one --changed file")
            sys.exit(1)
        selected = retr.retrieve_procedure(args.changed[0], args.procedure)
        if not selected:
            print(f"ERROR: procedure '{args.procedure}' not found in {args.changed[0]}")
            sys.exit(1)
    else:
        selected = retr.retrieve(args.changed, mode=args.mode, import_depth=args.depth)
    ctx = assemble(selected)
    if args.preflight:
        abs_files = [os.path.join(args.repo, f) for f in args.changed]
        pre = run_preflight(abs_files)
        ctx = (
            "# === DETERMINISTIC PRE-FLIGHT (static analyzers) ===\n"
            f"{pre}\n\n# === RETRIEVED CODE CONTEXT ===\n{ctx}"
        )
    modules = sorted({c.module for c in selected})
    print(f"Mode:        {'procedure' if args.procedure else args.mode}")
    print(f"Modules:     {modules}")
    print(f"Chunks:      {len(selected)}")
    print(f"Tokens(est): {estimate(ctx)}")
    if args.show:
        print("\n----- assembled context -----\n")
        print(ctx)


def cmd_summary(args):
    """Lightweight, token-cheap analysis: risk map + pre-flight."""
    idx = load_index(args.repo, args.index)
    report = summarize(idx, files=args.files, top_n=args.top)
    print(report)
    print(f"\n[summary tokens(est): {estimate(report)}]")


def main():
    p = argparse.ArgumentParser(prog="crl", description="Token-efficient code review pipeline")
    sub = p.add_subparsers(dest="cmd")

    pi = sub.add_parser("index", help="build and cache the code index")
    pi.add_argument("repo")
    pi.add_argument("--index", default=None)
    pi.set_defaults(func=cmd_index)

    ps = sub.add_parser("summary", help="lightweight analysis: size/complexity map + pre-flight (no full source dump)")
    ps.add_argument("repo")
    ps.add_argument("--files", nargs="*", default=None,
                    help="restrict scope to these files (default: whole repo)")
    ps.add_argument("--top", type=int, default=15,
                    help="how many top procedures by risk to list")
    ps.add_argument("--index", default=None)
    ps.set_defaults(func=cmd_summary)

    pr = sub.add_parser("review", help="retrieve targeted context for changed files")
    pr.add_argument("repo")
    pr.add_argument("--changed", nargs="+", required=True)
    pr.add_argument("--mode", choices=["module", "function"], default="module")
    pr.add_argument("--depth", type=int, default=1)
    pr.add_argument("--index", default=None)
    pr.add_argument("--show", action="store_true")
    pr.add_argument("--preflight", action="store_true",
                    help="run free static analyzers (ruff/mypy/semgrep/vba-lint) on changed files before review")
    pr.add_argument("--procedure", default=None,
                    help="review a single named procedure (surgical, within-file)")
    pr.set_defaults(func=cmd_review)

    args = p.parse_args()
    if not getattr(args, "func", None):
        p.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
