"""Tests for v12b skills management (skills_mgmt.py)."""
import os
import tempfile
import unittest

from toks import skills_mgmt


def make_skill(root, dirname, name, desc, version="1.0.0", lines=20):
    d = os.path.join(root, dirname)
    os.makedirs(d, exist_ok=True)
    body = "\n".join("instruction line {}".format(i) for i in range(lines))
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write("---\nname: {}\nversion: {}\ndescription: \"{}\"\n---\n\n{}\n".format(
            name, version, desc, body))


class TestSkillsMgmt(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_scan_finds_skills(self):
        make_skill(self.root, "alpha", "alpha", "Use when doing alpha work tasks")
        skills = skills_mgmt.scan_skills(self.root)
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["name"], "alpha")

    def test_skips_hidden_and_archive_dirs(self):
        make_skill(os.path.join(self.root, ".hidden"), "h", "hid",
                   "Use when hidden work needed")
        make_skill(os.path.join(self.root, ".archive"), "a", "arch",
                   "Use when archived work needed")
        self.assertEqual(skills_mgmt.scan_skills(self.root), [])

    def test_duplicate_name_flagged(self):
        make_skill(self.root, "dirA", "same-name", "Use when alpha work happens")
        make_skill(self.root, "dirB", "same-name", "Use when beta work happens")
        issues = skills_mgmt.find_issues(skills_mgmt.scan_skills(self.root))
        self.assertTrue(any(i["type"] == "DUPLICATE" for i in issues))

    def test_near_dup_description_flagged(self):
        desc = "Auto-generated from verified pattern 'X' — comprehensive workflow"
        make_skill(self.root, "dA", "skill-a", desc + " one")
        make_skill(self.root, "dB", "skill-b", desc + " two")
        issues = skills_mgmt.find_issues(skills_mgmt.scan_skills(self.root))
        self.assertTrue(any(i["type"] == "NEAR-DUP" for i in issues))

    def test_vague_trigger_flagged(self):
        make_skill(self.root, "vague", "vague-skill", "stuff")
        issues = skills_mgmt.find_issues(skills_mgmt.scan_skills(self.root))
        self.assertTrue(any(i["type"] == "VAGUE-TRIGGER" for i in issues))

    def test_oversized_flagged(self):
        make_skill(self.root, "big", "big-skill",
                   "Use when big work needs many lines of guidance", lines=600)
        issues = skills_mgmt.find_issues(skills_mgmt.scan_skills(self.root))
        self.assertTrue(any(i["type"] == "OVERSIZED" and i["skill"] == "big-skill"
                            for i in issues))

    def test_clean_skill_no_issues(self):
        make_skill(self.root, "ok", "ok-skill",
                   "Use when compressing tool output before sending to model")
        self.assertEqual(skills_mgmt.find_issues(
            skills_mgmt.scan_skills(self.root)), [])

    def test_index_one_line_per_skill(self):
        make_skill(self.root, "a1", "skill-a", "Use when alpha tasks appear")
        idx = skills_mgmt.build_index(skills_mgmt.scan_skills(self.root))
        self.assertEqual(idx.count("\n"), 0)
        self.assertTrue(idx.startswith("skill-a — Use when"))

    def test_search_finds_match(self):
        make_skill(self.root, "c1", "compressor",
                   "Compress JSON payloads and drop null fields")
        skills = skills_mgmt.scan_skills(self.root)
        self.assertEqual(skills_mgmt.search_index(skills, "compress json"),
                         ["compressor"])

    def test_report_renders(self):
        r = skills_mgmt.format_report("root", [], [])
        self.assertIn("skills audit", r)


if __name__ == "__main__":
    unittest.main()
