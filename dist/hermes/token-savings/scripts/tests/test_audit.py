"""Session self-audit (v8) - deterministic standing-rule violation flags."""
import unittest

from toks import audit


CLEAN = "short reply one\n\nshort reply two\n"


class TestAudit(unittest.TestCase):
    def test_clean_transcript(self):
        self.assertEqual(audit.audit_session(CLEAN), [])

    def test_re_read_detected(self):
        big = "x" * 300
        f = audit.audit_session(big + "\n\n" + big)
        self.assertTrue(any(x["rule"] == "re-read" for x in f))

    def test_prose_bloat_detected(self):
        block = "\n".join("line {}".format(i) for i in range(50))
        f = audit.audit_session(block)
        self.assertTrue(any(x["rule"] == "prose-bloat" for x in f))

    def test_loop_detected(self):
        text = "run toks dedup\nrun toks dedup\nrun toks dedup\n"
        f = audit.audit_session(text)
        self.assertTrue(any(x["rule"] == "loop" for x in f))

    def test_bad_json_detected(self):
        f = audit.audit_session('{"a": 1,}')
        self.assertTrue(any(x["rule"] == "json" for x in f))

    def test_format_report(self):
        self.assertIn("CLEAN", audit.format_report([]))
        r = audit.format_report([{"rule": "loop", "line": 3, "detail": "x"}])
        self.assertIn("1 finding", r)


if __name__ == "__main__":
    unittest.main()