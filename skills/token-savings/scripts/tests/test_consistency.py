"""End-to-end consistency: one unified pipeline across communication scenarios.

Each scenario routes through the SAME entry point (dedup -> safe-mode ->
multi-surface compress -> quality gate), proving the skill applies consistently
whether the surface is code review, chat/output, or RAG retrieval.
"""
import json
import os
import tempfile
import unittest

from toks import dedup, compress, astrip, safemode, measure, protect


def unified_compress(raw, kind="text", cache=None):
    """Single entry point used across ALL scenarios (no per-surface forks)."""
    if cache is not None:
        ref = cache.ref(raw)
        if ref is not None:
            return ref, True  # 100% saving, no quality risk
    if not safemode.should_compress(raw):
        return raw, False  # safe-mode pass-through, 0% compression
    if kind == "json":
        out = protect.compress_protected(
            raw, lambda t: compress.compress_json(json.loads(t))
        )
    elif kind == "code":
        out = protect.compress_protected(raw, lambda t: astrip.astrip(t, lang="py"))
    elif kind == "bash":
        out = compress.trim_bash(raw, max_lines=40)
    else:
        out = raw
    return out, True


class TestConsistency(unittest.TestCase):
    def setUp(self):
        self.cache = dedup.DedupCache(cache_path=os.path.join(tempfile.mkdtemp(), "d.json"))

    def _check(self, raw, kind, protected=None):
        before = raw
        if protected:
            before = raw.replace("__PROT__", f"[[KEEP]]{protected}[[/KEEP]]")
        out, saved = unified_compress(before, kind=kind, cache=self.cache)
        if protected:
            q = measure.quality_gate(before, out)
            self.assertTrue(q["pass"], f"protected lost: {q['missing']}")
        self.assertLessEqual(len(out), len(before))
        return out

    def test_code_review_scenario(self):
        # Realistically large module: 6 functions with multi-line bodies.
        code = "\n".join(
            [
                f"def func_{i}(a, b):\n"
                f"    # doc {i}\n"
                f"    result = a + b\n"
                f"    for _ in range(10):\n"
                f"        result += 1\n"
                f"    return result\n"
                for i in range(6)
            ]
        )
        out = self._check(code, "code")
        self.assertIn("def func_0", out)
        self.assertIn("[body omitted]", out)
        self.assertLess(len(out), len(code))  # AST stripping reduces large input

    def test_chat_output_scenario(self):
        text = "blah " * 200 + "__PROT__"
        out = self._check(text, "text", "EXACT_PHRASE_42")
        self.assertIn("EXACT_PHRASE_42", out)

    def test_rag_json_scenario(self):
        payload = json.dumps(
            {
                "answer": "Paris",
                "debug": "trace",
                "citation": "[[KEEP]]src#42[[/KEEP]]",
                "nullfield": None,
            }
        )
        out, _ = unified_compress(payload, kind="json", cache=self.cache)
        self.assertIn("src#42", out)
        self.assertNotIn("debug", out)
        self.assertNotIn("nullfield", out)

    def test_safemode_passthrough(self):
        secret = "api_key = 'ABCDEFGH12345678'"
        out, saved = unified_compress(secret, kind="text", cache=self.cache)
        self.assertEqual(out, secret)  # unchanged, 0% compression
        self.assertFalse(saved)

    def test_dedup_shortcut(self):
        raw = "very long repeated context " * 50
        unified_compress(raw, "text", cache=self.cache)  # first: store
        out2, saved = unified_compress(raw, "text", cache=self.cache)
        self.assertTrue(out2.startswith("§ref:"))
        self.assertTrue(saved)


if __name__ == "__main__":
    unittest.main()
