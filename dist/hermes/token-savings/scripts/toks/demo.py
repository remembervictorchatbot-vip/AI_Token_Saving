"""Quick self-test demo for the toks toolkit.

Exercises every surface with a tiny in-memory example and prints PASS/FAIL
per surface. Used by the `toks demo` CLI subcommand and CI smoke test.
"""
from toks import dedup, compress, astrip, safemode, hygiene, measure, checkpoint, mdnorm, toolaudit, output


def run_demo():
    ok = True
    dc = dedup.DedupCache()
    dc.reset()
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

    res = toolaudit.audit_connectors(toolaudit.sample_manifest(), keep=["notion"])
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
