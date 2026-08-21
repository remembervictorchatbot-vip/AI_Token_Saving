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


def main():
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
    args = p.parse_args()

    if args.cmd == "dedup":
        dc = dedup.DedupCache()
        if args.reset:
            dc.reset(); print("reset")
        else:
            r = dc.ref(args.text)
            print(r if r else "[FIRST TIME - keep full content]")
    elif args.cmd == "compress-json":
        print(compress.compress_json(json.loads(args.text)))
    elif args.cmd == "trim-bash":
        print(compress.trim_bash(args.text, args.max_lines))
    elif args.cmd == "summarize-grep":
        print(compress.summarize_grep(args.text, args.top))
    elif args.cmd == "astrip":
        print(astrip.astrip(args.text, args.lang, strip_comments=not args.keep_comments))
    elif args.cmd == "safemode":
        print(safemode.risk_level(args.text), "| compress:" , safemode.should_compress(args.text))
    elif args.cmd == "hygiene":
        rep = hygiene.hygiene_report(path=args.path) if args.path else hygiene.hygiene_report(lines=len(args.text.splitlines()))
        print(rep)
    elif args.cmd == "measure":
        print(measure.est_tokens(args.text))
    elif args.cmd == "quality-gate":
        print(measure.quality_gate(args.before, args.after))
    elif args.cmd == "checkpoint":
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
    elif args.cmd == "protect":
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
    elif args.cmd == "mdnorm":
        if args.source == "md":
            print(mdnorm.normalize_markdown(args.text))
        else:
            print(mdnorm.html_to_markdown(args.text))
    elif args.cmd == "toolaudit":
        raw = args.text
        if args.manifest:
            with open(args.manifest, "r", encoding="utf-8") as fh:
                raw = fh.read()
        if not raw:
            raw = _sample_manifest()
        keep = [k for k in args.keep.split("|") if k] if args.keep else None
        res = toolaudit.audit_connectors(
            raw, threshold_pct=args.threshold_pct,
            abs_token_floor=args.abs_floor, keep=keep,
        )
        print(toolaudit.format_report(res))
    elif args.cmd == "output-budget":
        print(f"{args.task}: max {output.budget(args.task)} lines (O-2)")
    elif args.cmd == "output-json":
        print("VALID" if output.valid_json(args.text) else "INVALID (O-1: don't emit)")
    elif args.cmd == "output-table":
        header = args.header.split("|")
        rows = [r.split("|") for r in args.rows.split(";")] if args.rows else []
        print(output.table_lines(header, rows))
    elif args.cmd == "selftest":
        import unittest

        scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        tests_dir = os.path.join(scripts_dir, "tests")
        suite = unittest.TestLoader().discover(tests_dir)
        res = unittest.TextTestRunner(verbosity=2).run(suite)
        print("\nSELFTEST:", "PASS" if res.wasSuccessful() else "FAIL")
        sys.exit(0 if res.wasSuccessful() else 1)
    elif args.cmd == "demo":
        run_demo()
    else:
        p.print_help()


def _sample_manifest():
    return json.dumps({
        "connectors": [
            {"name": "kdocs", "tools": [
                {"name": "wpp.create_presentation", "schema_chars": 1800},
                {"name": "wpp.read_presentation", "schema_chars": 1500},
                {"name": "sheet.create", "schema_chars": 1600},
            ]},
            {"name": "feishu", "tool_count": 60, "avg_schema_chars": 1200},
            {"name": "notion", "tool_count": 12, "avg_schema_chars": 900},
            {"name": "agent-mail", "tool_count": 8, "avg_schema_chars": 700},
        ]
    })


def run_demo():
    ok = True
    dc = dedup.DedupCache(); dc.reset()
    r1 = dc.ref("SELECT * FROM users")
    r2 = dc.ref("SELECT * FROM users")
    ok = ok and (r1 is None) and (r2 is not None) and r2.startswith("\u00a7ref:")
    print("dedup:", "PASS" if ok else "FAIL", dc.stats())

    j = compress.compress_json({"a": 1, "b": None, "debug": "x", "c": {"d": 2}})
    ok = ok and ("null" not in j) and ("debug" not in j)
    print("compress-json:", "PASS" if ok else "FAIL", j)

    out = compress.trim_bash("\n".join(["line"] * 10), max_lines=5)
    ok = ok and "collapsed" in out
    print("trim-bash:", "PASS" if ok else "FAIL")

    code = "def f(x):\n    # comment\n    return x+1\n\nclass C:\n    def m(self):\n        pass\n"
    a = astrip.astrip(code)
    ok = ok and "[body omitted]" in a and "f(x)" in a and "class C" in a
    print("astrip:", "PASS" if ok else "FAIL")

    sec = safemode.risk_level("api_key = 'ABCDEFGH12345678'")
    ok = ok and sec == "unsafe"
    print("safemode:", "PASS" if ok else "FAIL", sec)

    h = hygiene.hygiene_report(lines=400)
    ok = ok and h["recommend_split"] is True
    print("hygiene:", "PASS" if ok else "FAIL", h["lines"])

    q = measure.quality_gate("x [[KEEP]]secret123[[/KEEP]] y", "x [[KEEP]]secret123[[/KEEP]] y")
    ok = ok and q["pass"]
    print("quality-gate:", "PASS" if ok else "FAIL", q)

    blk = checkpoint.emit_checkpoint({"Active task": "X", "Decisions": ["d1"], "Next steps": ["n1"]})
    parsed = checkpoint.parse_checkpoint(blk)
    ok = ok and parsed.get("Active task") == "X"
    print("checkpoint:", "PASS" if ok else "FAIL")

    # Phase 2 tools
    html = "<html><head><style>x</style></head><body><nav>menu</nav><h1>Title</h1><p>Hello <b>world</b></p><script>evil()</script></body></html>"
    md = mdnorm.html_to_markdown(html)
    ok = ok and "# Title" in md and "**world**" in md and "menu" not in md and "evil" not in md
    print("mdnorm:", "PASS" if ok else "FAIL")

    res = toolaudit.audit_connectors(_sample_manifest(), keep=["notion"])
    ok = ok and res["disconnected_any"] is False and "notion" not in res["review_candidates"]
    print("toolaudit:", "PASS" if ok else "FAIL", "review:", res["review_candidates"])

    # v6 output economics (O-1..O-5)
    ok = ok and output.budget("verdict") == 1 and output.budget("unknown") == output.budget("chat_reply")
    print("output-budget:", "PASS" if ok else "FAIL", output.budget("verdict"), output.budget("report"))
    ok = ok and output.valid_json('{"a":1}') and not output.valid_json('{"a":1')
    print("output-json:", "PASS" if ok else "FAIL")
    tbl = output.table_lines(["id", "name"], [[1, "Alice"], [2, "Bob"]])
    ok = ok and tbl.count("id") == 1 and "Alice" in tbl and "Bob" in tbl
    print("output-table:", "PASS" if ok else "FAIL")
    ac = output.AnswerCache()
    ac.put("q", "ctx", "answer1")
    ok = ok and ac.get("q", "ctx") == "answer1" and ac.get("q", "ctx", fresh=True) is None \
        and ac.get("q", "other") is None
    print("output-cache:", "PASS" if ok else "FAIL", ac.stats())

    print("\nALL:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
