"""Regression guard: token-efficient-code-review must remain a pointer-only skill.

Its own SKILL.md declares it CONSOLIDATED into token-savings. Any scripts/
directory there is dead duplication and must not return.
"""
import os
import unittest


class TestNoDuplicateSkills(unittest.TestCase):
    def test_pointer_skill_has_no_scripts(self):
        # Resolve repo root by walking up until we find skills/token-efficient-code-review
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = here
        for _ in range(8):
            if os.path.isdir(os.path.join(repo_root, "skills", "token-efficient-code-review")):
                break
            parent = os.path.dirname(repo_root)
            if parent == repo_root:
                break
            repo_root = parent
        pointer_dir = os.path.join(repo_root, "skills", "token-efficient-code-review")
        # Skip when running from a distribution bundle (e.g. dist/hermes/) where the
        # pointer skill is not co-located — this guard only applies to the source repo.
        if not os.path.isdir(pointer_dir):
            self.skipTest("not running from source repo (bundle context)")
        entries = sorted(os.listdir(pointer_dir))
        self.assertEqual(
            entries, ["SKILL.md"],
            f"token-efficient-code-review must contain only SKILL.md, found: {entries}",
        )
        scripts_dir = os.path.join(pointer_dir, "scripts")
        self.assertFalse(
            os.path.isdir(scripts_dir),
            f"dead scripts/ directory must not exist at {scripts_dir}",
        )


if __name__ == "__main__":
    unittest.main()
