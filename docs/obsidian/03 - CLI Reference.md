---
tags: [toks crl]
---

# 03 - CLI Reference

All commands are pure stdlib, deterministic, and location-independent
(bin/toks resolves its skill dir via TOKS_SKILL_DIR -> HERMES_SKILL_DIR ->
autodetect). Run from anywhere.

## toks (general toolkit)

```bash
toks selftest                 # FULL suite (currently 132 tests) - must stay GREEN
toks demo                     # quick self-tests
toks measure --text "..."     # est. tokens (chars/4) - diagnostic
toks dedup --text "$(cat file.txt)"        # ref or [FIRST TIME]
toks astrip --text "$CODE" --lang py       # signature skeleton
toks safemode --text "$TEXT"               # unsafe|caution|safe
toks hygiene --path file.py                # >300 lines? split?
toks compress-json --text '{"a":1,"b":null}'
toks trim-bash --text "$OUTPUT" --max-lines 40
toks summarize-grep --text "$GREP" --top 10
toks protect --text "..." --mode code|json|text   # guarantees protected zones survive
toks quality-gate --before "..." --after "..."
toks checkpoint --emit --active-task "..." --decisions "d1|d2" --open-questions "q1|q2" --lessons "l1"
toks mdnorm --text "$HTML" --source html   # HTML -> clean Markdown (USE-8)
toks mdnorm --text "$MD" --source md       # normalize messy Markdown
toks toolaudit --manifest conns.json --keep "feishu|notion"   # audit tool surface, recommend-only (USE-7)
toks output-budget --task analysis         # O-2 ceiling in lines
toks output-json --text '{"a":1'           # O-1 gate: VALID / INVALID
toks output-table --header "id|name" --rows "1|Alice;2|Bob"   # O-1 header-once table
toks --help
```

The resume helper is a library: 'from toks import resume;
resume.write_resume(state)' / 'resume.read_resume()'.

## crl (code-review retrieval engine)

```bash
python -m crl.cli index <repo>                            # index once, cached
python -m crl.cli review <repo> --changed app/utils.py --mode function --show
python -m crl.cli summary <repo> --files module.txt --top 12   # cheap tier
python crl_demo.py                                        # token-savings table
```

Index once, retrieve only the changed closure (module- or symbol-level),
optional deterministic pre-flight (ruff/mypy/semgrep/vba-lint), then LLM
review on the trimmed context. Function-mode hits ~85% input saved on leaf
changes (measured in crl demo: 85.2% / 47.3%).

## Notes

- 'bin/toks' works from any cwd; without PATH use 'bin/toks <cmd>' from the
  skill root, or TOKS_SKILL_DIR=/path bin/toks <cmd>.
- The older 'python -m toks.cli <cmd>' form works from scripts/ directly.
- Full suite lives in scripts/tests/ and runs via 'python -m toks.cli selftest'.

See also: [[06 - Adapters]] (filter env vars), [[11 - Development]] (tests).