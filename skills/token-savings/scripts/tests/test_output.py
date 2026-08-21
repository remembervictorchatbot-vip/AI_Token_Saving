"""Output-side economics (v6, O-1..O-5)."""
import unittest

from toks import output


class TestBudget(unittest.TestCase):
    def test_known_types(self):
        self.assertEqual(output.budget("verdict"), 1)
        self.assertEqual(output.budget("classification"), 3)
        self.assertEqual(output.budget("chat_reply"), 15)
        self.assertEqual(output.budget("report"), 70)

    def test_unknown_falls_back_to_chat(self):
        self.assertEqual(output.budget("no_such_task"), output.budget("chat_reply"))

    def test_data_only_zero(self):
        self.assertEqual(output.budget("data_only"), 0)


class TestValidJson(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(output.valid_json('{"a":1,"b":[1,2]}'))
        self.assertTrue(output.valid_json("[1,2,3]"))
        self.assertTrue(output.valid_json('"just a string"'))

    def test_invalid(self):
        self.assertFalse(output.valid_json('{"a":1'))
        self.assertFalse(output.valid_json("not json"))
        self.assertFalse(output.valid_json(""))


class TestTableLines(unittest.TestCase):
    def test_header_once_rows_streamed(self):
        tbl = output.table_lines(["id", "name"], [[1, "Alice"], [2, "Bob"]])
        self.assertEqual(tbl.count("id"), 1)
        self.assertIn("Alice", tbl)
        self.assertIn("Bob", tbl)
        self.assertIn("-", tbl)  # separator row

    def test_empty_rows(self):
        tbl = output.table_lines(["a", "b"], [])
        self.assertIn("a", tbl)
        self.assertEqual(tbl.count("a"), 1)

    def test_empty_header(self):
        self.assertEqual(output.table_lines([], [[1]]), "")

    def test_ragged_rows_padded(self):
        tbl = output.table_lines(["a", "b", "c"], [[1, 2]])
        self.assertIn("1", tbl)
        self.assertIn("2", tbl)

    def test_compact_than_repeated_json(self):
        header = ["id", "name", "role"]
        rows = [[1, "Alice", "eng"], [2, "Bob", "pm"], [3, "Cy", "qa"]]
        tbl = output.table_lines(header, rows)
        self.assertLess(len(tbl), 300)


class TestAnswerCache(unittest.TestCase):
    def setUp(self):
        self.cache = output.AnswerCache()

    def test_miss_then_hit(self):
        self.assertIsNone(self.cache.get("q", "ctx"))
        self.cache.put("q", "ctx", "answer1")
        self.assertEqual(self.cache.get("q", "ctx"), "answer1")

    def test_fresh_bypasses_cache(self):
        self.cache.put("q", "ctx", "answer1")
        self.assertIsNone(self.cache.get("q", "ctx", fresh=True))

    def test_different_context_misses(self):
        self.cache.put("q", "ctx", "answer1")
        self.assertIsNone(self.cache.get("q", "other"))

    def test_different_query_misses(self):
        self.cache.put("q1", "ctx", "answer1")
        self.assertIsNone(self.cache.get("q2", "ctx"))

    def test_put_overwrites(self):
        self.cache.put("q", "ctx", "old")
        self.cache.put("q", "ctx", "new")
        self.assertEqual(self.cache.get("q", "ctx"), "new")

    def test_stats(self):
        self.cache.put("q1", "c", "a")
        self.cache.put("q2", "c", "b")
        self.assertEqual(self.cache.stats()["entries"], 2)


if __name__ == "__main__":
    unittest.main()
