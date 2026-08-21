"""Robustness sweep (v10 audit): every CLI subcommand must not crash
on normal + hostile input. Guards regressions like the old
toolaudit --manifest traceback.
"""
import io
import sys
import unittest

from toks import cli

NL = chr(10)
BIG = '{"items": [' + ",".join('{"id": %d, "meta": null, "debug": "x"}' % i for i in range(100)) + "]}"

CASES = [
    ["dedup", "--text", "hello"],
    ["dedup", "--text", "hello", "--reset"],
    ["dedup", "--diff", "--text", "a" + NL + "b"],
    ["compress-json", "--text", BIG],
    ["compress-json", "--text", "[1,2,3]"],
    ["trim-bash", "--text", "a" + NL + "b" + NL + "a"],
    ["summarize-grep", "--text", "x" + NL + "y"],
    ["astrip", "--text", "def broken(:", "--lang", "py"],
    ["safemode", "--text", "password = s3cr3t_value_xyz"],
    ["hygiene", "--text", "x" + NL + "x"],
    ["measure", "--text", "hello"],
    ["quality-gate", "--before", "id:1", "--after", "x", "--facts", "id:1"],
    ["checkpoint", "--auto", "--text", "work" + NL + "TODO: verify"],
    ["protect", "--text", "a [[KEEP]]b[[/KEEP]] c", "--mode", "text"],
    ["mdnorm", "--text", "<html><h1>hi</h1></html>", "--source", "html"],
    ["toolaudit", "--manifest", "/nonexistent/manifest.json"],
    ["toolaudit", "--text", '{"connectors":[{"name":"a","tools":1,"calls":1}]}'],
    ["output-budget", "--task", "bogus"],
    ["output-json", "--text", '{"a":1,}'],
    ["output-table", "--header", "a|b", "--rows", "1|2;3|4"],
    ["cost-estimate", "--steps", "2", "--ctx-chars", "1000"],
    ["surface", "--text", "def f(): pass", "--lang", "py"],
    ["surface", "--text", '{"a": {"b": 1}}', "--lang", "json"],
    ["check-syntax", "--text", "```", "--lang", "md"],
    ["audit-session", "--text", "a" + NL + NL + "b"],
    ["input-gate", "--text", "tiny"],
    ["input-meter", "--text", "a" + NL + NL + "b"],
    ["output-gate", "--text", "x", "--task", "verdict"],
    ["autopilot", "--text", "a" + NL + NL + "b"],
    ["doctor"],
    ["setup"],
]


class TestRobustness(unittest.TestCase):
    def test_no_crash_on_any_subcommand(self):
        for args in CASES:
            old = sys.argv
            sys.argv = ["toks"] + args
            out, err = io.StringIO(), io.StringIO()
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = out, err
            try:
                cli.main()
            except SystemExit as e:
                # 0 ok, 1 audit violations, 2 clean file errors - all by design
                self.assertIn(e.code, (0, 1, 2), "unexpected exit for {}".format(args))
            except Exception as e:
                self.fail("{} crashed: {}: {}".format(args, type(e).__name__, e))
            finally:
                sys.stdout, sys.stderr = old_out, old_err
                sys.argv = old

    def test_missing_manifest_is_clean_error(self):
        old = sys.argv
        sys.argv = ["toks", "toolaudit", "--manifest", "/nonexistent/manifest.json"]
        out, err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        with self.assertRaises(SystemExit) as cm:
            cli.main()
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("cannot read", err.getvalue())
        sys.stdout, sys.stderr = old_out, old_err
        sys.argv = old


if __name__ == "__main__":
    unittest.main()