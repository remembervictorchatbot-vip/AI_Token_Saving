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
    python -m toks.cli dedup --diff --text "..."     # delta re-read (v8)
    python -m toks.cli cost-estimate --steps 5 --ctx-chars 120000   # G1 preflight
    python -m toks.cli surface --path file.py        # read-me-first (v8)
    python -m toks.cli check-syntax --text "..." --lang py   # O-6 gate
    python -m toks.cli audit-session --file transcript.txt   # self-audit (v8)
"""
import argparse
import json
import os
import sys

from toks import dedup, compress, measure, checkpoint, astrip, safemode, hygiene, protect, mdnorm, toolaudit, output, cost, surface, check, audit, gate, input_meter, autopilot, doctor  # noqa: E402
from toks import pd, route, isolate  # noqa: E402  (v11)
from toks import read_cache, memory_decay  # noqa: E402  (v11b)
from toks import auto  # noqa: E402  (v11c smart auto-compress)
from toks import toolsearch  # noqa: E402  (v11d tool-search surface)
from toks import discover  # noqa: E402  (v12 live surface discovery)
from toks.demo import run_demo


def build_parser():
    """Construct and return the top-level ArgumentParser with all subcommands."""
    p = argparse.ArgumentParser(prog="toks", description="Token-saving toolkit")
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("dedup")
    d.add_argument("--text", required=True)
    d.add_argument("--reset", action="store_true")
    d.add_argument("--diff", action="store_true", help="delta re-read: ref on exact repeat, changed-line hunks on change")

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
    qg.add_argument("--facts", default="", help="pipe-separated facts to verify, e.g. id:123|name:foo")

    cp = sub.add_parser("checkpoint")
    cp.add_argument("--emit", action="store_true")
    cp.add_argument("--auto", action="store_true", help="auto-extract open work from --text (v10)")
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

    ce = sub.add_parser("cost-estimate")
    ce.add_argument("--steps", type=int, default=5)
    ce.add_argument("--ctx-chars", type=int, default=120000)
    ce.add_argument("--out-chars", type=int, default=4000)
    ce.add_argument("--price-per-mtok", type=float,
                    default=float(os.environ.get("TOKS_PRICE_PER_MT", "1.0")))
    ce.add_argument("--peak", action="store_true", default=True)
    ce.add_argument("--idle", action="store_true")

    sf = sub.add_parser("surface")
    sf.add_argument("--text", default="")
    sf.add_argument("--path", default="")
    sf.add_argument("--lang", default="auto", choices=["auto", "py", "json", "md", "conf"])

    cs = sub.add_parser("check-syntax")
    cs.add_argument("--text", required=True)
    cs.add_argument("--lang", default="py", choices=["py", "json", "md"])

    au = sub.add_parser("audit-session")
    au.add_argument("--text", default="")
    au.add_argument("--file", default="")

    ig = sub.add_parser("input-gate")
    ig.add_argument("--text", default="")
    ig.add_argument("--file", default="")
    ig.add_argument("--no-dedup", action="store_true")
    ig.add_argument("--min-compress", type=int, default=80)

    im = sub.add_parser("input-meter")
    im.add_argument("--text", default="")
    im.add_argument("--file", default="")

    og = sub.add_parser("output-gate")
    og.add_argument("--text", required=True)
    og.add_argument("--task", default="chat_reply")

    ap = sub.add_parser("autopilot")
    ap.add_argument("--text", default="")
    ap.add_argument("--file", default="")
    ap.add_argument("--task", default="chat_reply")

    sp = sub.add_parser("setup")
    sp.add_argument("--write-env", action="store_true")

    # v11: progressive-disclosure / tier-routing / sub-agent isolation
    pdp = sub.add_parser("pd")
    pdp.add_argument("--text", default="")
    pdp.add_argument("--file", default="")
    pdp.add_argument("--budget", type=int, default=30000)

    rp = sub.add_parser("route")
    rp.add_argument("--task", required=True)
    rp.add_argument("--base-cost", type=float, default=1.0)

    ip = sub.add_parser("isolate")
    ip.add_argument("--goal", required=True)
    ip.add_argument("--context", default="")
    ip.add_argument("--paths", default="")
    ip.add_argument("--contract", default="")

    # v11b: re-read suppression + hot-memory decay
    rc = sub.add_parser("read-cache")
    rc.add_argument("--path", required=True)
    rc.add_argument("--record", action="store_true")
    rc.add_argument("--reset", action="store_true")

    md_ = sub.add_parser("memory-decay")
    md_.add_argument("--file", required=True)
    md_.add_argument("--max-chars", type=int, default=400)
    md_.add_argument("--stale-days", type=int, default=30)

    ac = sub.add_parser("auto-compress")
    ac.add_argument("--text", default="")
    ac.add_argument("--file", default="")
    ac.add_argument("--min-ratio", type=float, default=0.3)
    ac.add_argument("--enforce-ratio", type=float, default=0.5)

    ts = sub.add_parser("tool-search")
    ts.add_argument("--manifest", default="")
    ts.add_argument("--text", default="")
    ts.add_argument("--query", default="")
    ts.add_argument("--keep", default="")
    ts.add_argument("--max-upfront", type=int, default=5)

    dv = sub.add_parser("discover")
    dv.add_argument("--live", action="store_true",
                    help="real MCP handshake (initialize + tools/list) per server")
    dv.add_argument("--timeout", type=int, default=20)

    sub.add_parser("doctor")

    sub.add_parser("selftest")
    sub.add_parser("demo")
    return p


# --- Handlers (one per subcommand) ---

def _resolve(path: str) -> str:
    """Resolve a relative --path/--manifest against the caller's cwd (bin/toks
    changes directory; TOKS_CALLER_CWD preserves where the user ran it)."""
    base = os.environ.get("TOKS_CALLER_CWD")
    if base and path and not os.path.isabs(path):
        return os.path.join(base, path)
    return path


def _read_text(path: str) -> str:
    """Read a file with a clean error instead of a traceback (v10 audit fix)."""
    try:
        with open(_resolve(path), "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as e:
        print("toks: cannot read {}: {}".format(path, e.strerror or e), file=sys.stderr)
        sys.exit(2)


def handle_dedup(args):
    dc = dedup.DedupCache()
    if args.reset:
        dc.reset()
        print("reset")
    elif args.diff:
        r = dc.diff_ref(args.text)
        print(r if r else "[FIRST TIME - keep full content]")
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
    extra = [f for f in args.facts.split("|") if f] if args.facts else None
    print(measure.quality_gate(args.before, args.after, extra_protected=extra))


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
    elif args.auto:
        print(checkpoint.emit_checkpoint(checkpoint.auto_state(args.text)))
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
        raw = _read_text(args.manifest)
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


def handle_cost_estimate(args):
    peak = not args.idle
    est = cost.estimate(args.steps, args.ctx_chars, args.out_chars,
                        price_per_mtok=args.price_per_mtok, peak=peak)
    print(cost.format_report(est))


def handle_surface(args):
    text = args.text
    if not text and args.path:
        text = _read_text(args.path)
    print(surface.surface(text, lang=args.lang, path=args.path))


def handle_check_syntax(args):
    ok, msg = check.validate(args.text, lang=args.lang)
    print(msg)


def handle_input_gate(args):
    text = args.text
    if not text and args.file:
        text = _read_text(args.file)
    print(gate.gate_content(text, use_dedup=not args.no_dedup,
                            min_compress=args.min_compress))


def handle_output_gate(args):
    print(output.gate_reply(args.text, task_type=args.task))


def handle_autopilot(args):
    text = args.text
    if not text and args.file:
        text = _read_text(args.file)
    print(autopilot.format_directives(autopilot.autopilot(text, task_type=args.task)))


def handle_doctor(args):
    print(doctor.format_report(doctor.run_checks()))


def handle_setup(args):
    print(doctor.setup_block())
    if args.write_env:
        print("\n[wrote] " + doctor.write_env())


def handle_input_meter(args):
    text = args.text
    if not text and args.file:
        text = _read_text(args.file)
    print(input_meter.format_report(input_meter.meter(text)))


def handle_audit_session(args):
    text = args.text
    if not text and args.file:
        text = _read_text(args.file)
    findings = audit.audit_session(text)
    print(audit.format_report(findings))
    if findings:
        sys.exit(1)


def handle_pd(args):
    text = args.text
    if not text and args.file:
        text = _read_text(args.file)
    print(pd.format_report(pd.audit_prompt(text, budget_tokens=args.budget)))


def handle_route(args):
    print(route.format_report(route.estimate(args.task, base_cost_per_task=args.base_cost)))


def handle_isolate(args):
    res = isolate.build_brief(args.goal, context=args.context,
                              paths=args.paths, output_contract=args.contract)
    print(isolate.format_report(res))


def handle_read_cache(args):
    rc_ = read_cache.ReadCache()
    if args.reset:
        rc_.reset()
        print("reset")
        return
    if args.record:
        print("recorded:", read_cache.ReadCache.record(rc_, _resolve(args.path)))
        return
    print(read_cache.format_report(rc_.check(_resolve(args.path))))


def handle_memory_decay(args):
    text = _read_text(args.file)
    print(memory_decay.format_report(memory_decay.audit_memory(
        text, max_chars=args.max_chars, stale_days=args.stale_days)))


def handle_auto_compress(args):
    text = args.text or _read_text(args.file) if (args.text or args.file) else ""
    res = auto.decide(text, min_ratio=args.min_ratio,
                      enforce_ratio=args.enforce_ratio)
    if res["verdict"] == "APPLY":
        print(res["out"])
        print("[auto-compress {} saved={}%]".format(
            res["verdict"], round(res["saved_ratio"] * 100)))
    else:
        print(auto.format_report(res))
        if res["verdict"] == "SHADOW":
            print(res["out"][:2000])


def handle_tool_search(args):
    raw = args.text
    if not raw and args.manifest:
        raw = _read_text(args.manifest)
    if not raw:
        raw = toolaudit.sample_manifest()
    if args.query:
        for name in toolsearch.search_tools(raw, args.query):
            print(name)
        return
    plan = toolsearch.plan_defer(
        raw, keep=[k for k in args.keep.split("|") if k],
        max_upfront=args.max_upfront)
    print(toolsearch.estimate_report(plan))
    print("--- search index (load this instead of full schemas) ---")
    print(toolsearch.build_index(raw))


def handle_discover(args):
    m = discover.discover(live=args.live, timeout=args.timeout)
    print(discover.format_report(m))


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
    "cost-estimate": handle_cost_estimate,
    "surface": handle_surface,
    "check-syntax": handle_check_syntax,
    "audit-session": handle_audit_session,
    "input-gate": handle_input_gate,
    "input-meter": handle_input_meter,
    "output-gate": handle_output_gate,
    "autopilot": handle_autopilot,
    "doctor": handle_doctor,
    "setup": handle_setup,
    "pd": handle_pd,
    "route": handle_route,
    "isolate": handle_isolate,
    "read-cache": handle_read_cache,
    "memory-decay": handle_memory_decay,
    "auto-compress": handle_auto_compress,
    "tool-search": handle_tool_search,
    "discover": handle_discover,
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
