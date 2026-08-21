"""Automatic input gate (v9) - save tokens without losing quality."""
import unittest

from toks import gate


class TestGate(unittest.TestCase):
    def test_short_passthrough(self):
        self.assertEqual(gate.gate_content("hi"), "hi")

    def test_empty_passthrough(self):
        self.assertEqual(gate.gate_content(""), "")

    def test_json_compressed(self):
        payload = '{"items": [' + ",".join(
            '{"id": %d, "meta": null, "debug": "x"}' % i for i in range(50)) + "]}"
        out = gate.gate_content(payload, use_dedup=False, min_compress=10)
        self.assertLess(len(out), len(payload))
        self.assertNotIn("debug", out)

    @staticmethod
    def _meaty_json():
        return '{"items": [' + ",".join(
            '{"id": %d, "meta": null, "debug": "x"}' % i for i in range(100)) + "]}"

    def test_marker_when_mark(self):
        out = gate.gate_content(self._meaty_json(), use_dedup=False, min_compress=10)
        self.assertTrue(out.startswith("[toks-gate"))
        self.assertIn("saved=", out)

    def test_no_marker_when_mark_false(self):
        out = gate.gate_content(self._meaty_json(), use_dedup=False, min_compress=10, mark=False)
        self.assertFalse(out.startswith("[toks-gate"))

    def test_idempotent(self):
        once = gate.gate_content(self._meaty_json(), use_dedup=False, min_compress=10)
        twice = gate.gate_content(once, use_dedup=False, min_compress=10)
        self.assertEqual(once, twice)

    def test_keep_survives(self):
        payload = '{"a": ' + "1" * 200 + ', "secret": "[[KEEP]]tok_abc_123[[/KEEP]]"}'
        out = gate.gate_content(payload, use_dedup=False, min_compress=10)
        self.assertIn("[[KEEP]]tok_abc_123[[/KEEP]]", out)

    def test_unsafe_passthrough(self):
        text = "password = s3cr3t_value_xyz\n" * 60
        out = gate.gate_content(text, use_dedup=False, min_compress=10)
        self.assertEqual(out, text)

    def test_never_grows(self):
        payload = '{"a": 1}'
        out = gate.gate_content(payload, use_dedup=False, min_compress=1)
        self.assertEqual(out, payload)

    def test_is_gated(self):
        self.assertTrue(gate.is_gated("[toks-gate v1 saved=10% tiers=json]"))
        self.assertFalse(gate.is_gated("plain text"))


if __name__ == "__main__":
    unittest.main()