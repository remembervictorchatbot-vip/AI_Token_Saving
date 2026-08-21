"""CLI entry for the toks toolkit. Run from the scripts/ dir:

    python -m toks.cli selftest        # FULL test suite (must stay GREEN)
    python -m toks.cli demo            # quick self-tests
    python -m toks.cli dedup --text "..."
    python -m toks.cli compress-json --text '{"a":1,"b":null,"debug":"x"}'
    python -m toks.cli trim-bash --text "$OUTPUT"
    python -m toks.cli summarize-grep --text "$GREP" --top 10
    python -m toks.cli astrip --text "$CODE" --lang py
    python -m toks.cli safemode --text "$TEXT"        # unsafe|caution|safe
    python -m toks.cli hygiene --text "$FILE_OR_CODE"
    python -m toks.cli measure --text "..."
    python -m toks.cli quality-gate --before "..." --after "..."
    python -m toks.cli protect --text "..." --mode code|json|text
    python -m toks.cli checkpoint --emit --active-task "..." --decisions "d1|d2"
"""
import argparse
import json
import os
import sys

from toks import dedup, compress, measure, checkpoint, astrip, safemode, hygiene, protect, mdnorm, toolaudit, output  # noqa: E402
from toks.demo import run_demo


def build_parser():
    """Construct and return the top-level ArgumentParser with all subcommands."""
    p = argparse.ArgumentParser(prog="toks", description="Token-saving toolkit")
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("dedup")
    d.add_argument("--text", required=True)
    d.add_argument("--reset", action="store_true")

    cj = sub.add_parser("compress-json")
    cj.add_argument("--text", required=True)

    tb = sub.add_parser("trim-bash")
    tb.add_argument("--text", required=True)
    tb.add_argument("--max-lines", type=int, default=40)

    sg = sub.add_parser("summarize-grep")
    sg.add_argument("--text", required=True)
    sg.add_argument("--top", type=int, default=10)

    ak = sub.add_parser("astrip")
    ak.add_argument("--text", required=True)
    ak.add_argument("--lang", default="py")
    ak.add_argument("--keep-comments", action="store_true")

    sm = sub.add_parser("safemode")
    sm.add_argument("--text", required=True)

    hy = sub.add_parser("hygiene")
    hy.add_argument("--text", default="")
    hy.add_argument("--path", default="")

    mt = sub.add_parser("measure")
    mt.add_argument("--text", required=True)

    qg = sub.add_parser("quality-gate")
    qg.add_argument("--before", required=True)
    qg.add_argument("--after", required=True)

    cp = sub.add_parser("checkpoint")
    cp.add_argument("--emit", action="store_true")
    cp.add_argument("--text", default="")
    cp.add_argument("--active-task", default="")
    cp.add_argument("--decisions", default="")
    cp.add_argument("--next-steps", default="")
    cp.add_argument("--open-questions", default="")
    cp.add_argument("--lessons", default="")

    pk = sub.add_parser("protect")
    pk.add_argument("--text", required=True)
    pk.add_argument("--mode", default="text", choices=["text", "code", "json"])

    md = sub.add_parser("mdnorm")
    md.add_argument("--text", required=True)
    md.add_argument("--source", default="html", choices=["html", "md"])

    ta = sub.add_parser("toolaudit")
    ta.add_argument("--text", default="")
    ta.add_argument("--manifest", default="")
    ta.add_argument("--threshold-pct", type=float, default=20.0)
    ta.add_argument("--abs-floor", type=int, default=5000)
    ta.add_argument("--keep", default="")

    ob = sub.add_parser("output-budget")
    ob.add_argument("--task", default="chat_reply")

    oj = sub.add_parser("output-json")
    oj.add_argument("--text", required=True)

    ot = sub.add_parser("output-table")
    ot.add_argument("--header", required=True)
    ot.add_argument("--rows", default="")

    sub.add_parser("selftest")
    sub.add_parser("demo")
    return p


# --- Handlers (one per subcommand) ---

def handle_dedup(args):
    dc = dedup.DedupCache()
    if args.reset:
        dc.reset()
        print("reset")
    else:
        r = dc.ref(args.text)
        print(r if r else "[FIRST TIME - keep full content]")


def handle_compress_json(args):
    print(compress.compress_json(json.loads(args.text)))


def handle_trim_bash(args):
    print(compress.trim_bash(args.text, args.max_lines))


def handle_summarize_grep(args):
    print(compress.summarize_grep(args.text, args.top))


def handle_astrip(args):
    print(astrip.astrip(args.text, args.lang, strip_comments=not args.keep_comments))


def handle_safemode(args):
    print(safemode.risk_level(args.text), "| compress:", safemode.should_compress(args.text))


def handle_hygiene(args):
    rep = hygiene.hygiene_report(path=args.path) if args.path else hygiene.hygiene_report(lines=len(args.text.splitlines()))
    print(rep)


def handle_measure(args):
    print(measure.est_tokens(args.text))


def handle_quality_gate(args):
    print(measure.quality_gate(args.before, args.after))


def handle_checkpoint(args):
    if args.emit:
        state = {
            "Active task": args.active_task,
            "Decisions": args.decisions.split("|") if args.decisions else [],
            "Next steps": args.next_steps.split("|") if args.next_steps else [],
            "Open questions": args.open_questions.split("|") if args.open_questions else [],
            "Lessons to carry": args.lessons.split("|") if args.lessons else [],
        }
        print(checkpoint.emit_checkpoint(state))
    else:
        print(checkpoint.parse_checkpoint(args.text))


def handle_protect(args):
    if args.mode == "json":
        out = protect.compress_protected(
            args.text, lambda t: compress.compress_json(json.loads(t))
        )
    elif args.mode == "code":
        out = protect.compress_protected(
            args.text, lambda t: astrip.astrip(t, lang="py")
        )
    else:
        out = protect.compress_protected(args.text, lambda t: t)
    print(out)


def handle_mdnorm(args):
    if args.source == "md":
        print(mdnorm.normalize_markdown(args.text))
    else:
        print(mdnorm.html_to_markdown(args.text))


def handle_toolaudit(args):
    raw = args.text
    if args.manifest:
        with open(args.manifest, "r", encoding="utf-8") as fh:
            raw = fh.read()
    if not raw:
        raw = toolaudit.sample_manifest()
    keep = [k for k in args.keep.split("|") if k] if args.keep else None
    res = toolaudit.audit_connectors(
        raw, threshold_pct=args.threshold_pct,
        abs_token_floor=args.abs_floor, keep=keep,
    )
    print(toolaudit.format_report(res))


def handle_output_budget(args):
    print(f"{args.task}: max {output.budget(args.task)} lines (O-2)")


def handle_output_json(args):
    print("VALID" if output.valid_json(args.text) else "INVALID (O-1: don't emit)")


def handle_output_table(args):
    header = args.header.split("|")
    rows = [r.split("|") for r in args.rows.split(";")] if args.rows else []
    print(output.table_lines(header, rows))


def handle_selftest(args):
    import unittest
    scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    tests_dir = os.path.join(scripts_dir, "tests")
    suite = unittest.TestLoader().discover(tests_dir)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    print("\nSELFTEST:", "PASS" if res.wasSuccessful() else "FAIL")
    sys.exit(0 if res.wasSuccessful() else 1)


def handle_demo(args):
    run_demo()


# Dispatch table: cmd name -> handler function
HANDLERS = {
    "dedup": handle_dedup,
    "compress-json": handle_compress_json,
    "trim-bash": handle_trim_bash,
    "summarize-grep": handle_summarize_grep,
    "astrip": handle_astrip,
    "safemode": handle_safemode,
    "hygiene": handle_hygiene,
    "measure": handle_measure,
    "quality-gate": handle_quality_gate,
    "checkpoint": handle_checkpoint,
    "protect": handle_protect,
    "mdnorm": handle_mdnorm,
    "toolaudit": handle_toolaudit,
    "output-budget": handle_output_budget,
    "output-json": handle_output_json,
    "output-table": handle_output_table,
    "selftest": handle_selftest,
    "demo": handle_demo,
}


def main():
    p = build_parser()
    args = p.parse_args()
    handler = HANDLERS.get(args.cmd)
    if handler:
        handler(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
