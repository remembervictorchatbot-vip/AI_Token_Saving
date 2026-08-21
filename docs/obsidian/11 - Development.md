---
tags: [dev]
---

# 11 - Development

## Test suite

```bash
cd skills/token-savings/scripts
python -m toks.cli selftest    # 164 tests, acceptance gate
python -m toks.cli demo        # quick smoke
cd ../../.. && python bench/run_bench.py --check   # benchmark regression gate
```

Any change to the skill must keep selftest GREEN.

## CI (GitHub Actions)

| Job | What it runs |
|---|---|
| test | selftest on Python 3.9 / 3.10 / 3.11 / 3.12 / 3.13, demo smoke, bin/toks --help from an unrelated cwd, bench --check, hermes bundle drift check (build_hermes_bundle.py --check) |
| lint | ruff check (E,F, E501 ignored - long lines are intentional) |
| windows-launcher | toks.bat --help + selftest on Windows |

## Building the Hermes bundle

```bash
python build_hermes_bundle.py           # regenerate from skills/
python build_hermes_bundle.py --check   # exit 1 if out of sync
```

Syncs scripts/ (toks, crl, tests, sample_repo, crl_demo.py) and bin/ (toks,
toks.bat). PRESERVES dist/hermes/token-savings/SKILL.md (hand-maintained
Hermes frontmatter + wording).

## Style

- [tool.ruff] in pyproject.toml: line-length 120, ignore E501, select E,F.
- Longer lines are intentional (fewer newline tokens) - this is a
  token-efficiency project.

## Contributing

- [CONTRIBUTING.md](../../CONTRIBUTING.md) - add/update tests in
  skills/token-savings/scripts/tests/, run selftest (164 tests, must pass).
- [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md), [SECURITY.md](../../SECURITY.md).

See also: [[05 - Skills]], [[06 - Adapters]].