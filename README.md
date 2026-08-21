# AI Token Saving — Unified Skills

A single, consolidated, quality-preserving **token-saving system** for AI coding
agents (WorkBuddy / Claude Code / Codex-style agents). It compresses input
context, strips output fluff, and keeps the learning loop alive across context
compaction — without dropping facts the user needs.

This repo publishes the skills so they can be shared, version-controlled, and
installed into any WorkBuddy-style agent.

**Measured tool-level savings (bench/REPORT.md): 49.6% aggregate** on
representative samples — dedup 98.3% · grep 92.5% · code-skeleton 79.2% ·
build-log trim 75.1% · data-only output 71.6% · JSON 43.0% · web→MD 28.4%.

> **MIT licensed** — see [LICENSE](LICENSE). Not affiliated with, endorsed by,
> or connected to any product or platform named in the compatibility matrix
> (WorkBuddy, Hermes Agent, Anthropic, OpenAI, Codex, Ollama, LM Studio, etc.).

---

## What's inside

```
skills/
  token-savings/                  ← THE unified skill (everything lives here)
    SKILL.md                      ← behavioral + compression + output discipline (USE-0..9, O-1..5)
    bin/toks                      ← portable launcher (any cwd: $TOKS_SKILL_DIR / $HERMES_SKILL_DIR / autodetect)
    scripts/
      toks/                       ← general token toolkit (stdlib Python, no deps)
        dedup.py                  ← file-hash dedup  (§ref:HASH§, ~70%+ over long sessions)
        compress.py               ← multi-surface compression (json/bash/grep/re-read)
        astrip.py                 ← AST extraction + comment stripping (60–90% input)
        safemode.py               ← never compress secrets / stack traces (stops hallucinations)
        protect.py                ← [[KEEP]] protected zones survive ANY compressor
        hygiene.py                ← <300-line files, tab/context hygiene
        measure.py                ← token estimate
        checkpoint.py, resume.py  ← durable RESUME.md checkpoint (loop survives)
        mdnorm.py                 ← HTML → clean Markdown for web/RAG ingestion (USE-8)
        toolaudit.py              ← connector tool-surface audit, recommend-only (USE-7)
        output.py                 ← output economics: budget/valid_json/table_lines/AnswerCache (O-1..O-5)
        boot.py                   ← portable skill-dir resolution
        cli.py                    ← CLI: demo / selftest / all subcommands
      crl/                        ← diff-aware code-review retrieval engine (folded in)
      tests/                      ← 131-test suite (run: toks selftest)
      crl_demo.py, sample_repo/   ← demos + fixtures
  engineering-discipline/         ← MANDATORY global SOP: phase decomposition + 7-step evidence gate + LESSONS.md
  rag-engineering/                ← RAG retrieval playbook (delegates token work)
  token-efficient-code-review/    ← pointer skill → use token-savings (crl folded in)
dist/
  hermes/token-savings/           ← Hermes Agent adapter (verified: installs + registers + enabled)
  system-prompt/token-savings-prompt.md ← condensed standing-rules bundle (harnesses w/o skill loader)
bench/
  run_bench.py, tasks.py          ← deterministic tool-level benchmark → REPORT.md
.github/workflows/ci.yml          ← pytest matrix 3.9–3.13 + demo + launcher + bench smoke
```

## Design principles (synthesized from 3 repos)

| Source repo | Kept (portable logic) | Rejected |
|---|---|---|
| **ojuschugh1/sqz** | content-hash dedup, lossless pipeline, entropy *safe mode* | Rust binary, PreToolUse rewiring |
| **alexgreensh/token-optimizer** | multi-surface compression, **auto-checkpoint**, quality gate, loop detection | hook daemon, SQLite dashboard |
| **vaibkumr/prompt-optimizer** | **protected zones** `[[KEEP]]`, entropy as *diagnostic* | blind entropy delete (drops accuracy) |

Plus behavioral control (fluff stripping, pre-code clarification, lazy-senior-dev
stdlib preference) and context hygiene (close tabs, <300-line files, fresh thread
every 8–10 turns).

## Targets & install

| Target | Status | Install |
|---|---|---|
| **WorkBuddy** | native, 131/131 tests, gated releases | `cp -R skills/* ~/.workbuddy/skills/` |
| **Hermes Agent** | verified (installs + registers + enabled) | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Codex / Claude Code / OpenCode-style** | behavioral rules port; needs AGENTS.md/skill conversion | copy `skills/token-savings`, ensure Python 3.9+ on PATH |
| **Any harness w/o skill loader** (e.g. custom DeepSeek harness, AI Studio, local agents) | system-prompt transplant | inject `dist/system-prompt/token-savings-prompt.md` at the top of the system prompt |
| Ollama / LM Studio (model servers) | no agent loop — only the condensed prompt applies | same system-prompt bundle |

The toolkit itself is portable: `bin/toks` resolves its own location via
`$TOKS_SKILL_DIR` → `$HERMES_SKILL_DIR` → autodetect. No hardcoded paths.

> Note: `dist/hermes/token-savings/scripts/` is a **generated bundle** (a copy of
> `skills/token-savings/scripts/`) so the Hermes skill stays self-contained when
> installed into `~/.hermes/skills/`. The source of truth is `skills/`.

## Verify

```bash
toks selftest           # 131 tests, all must pass (bin/toks from any cwd)
toks demo               # self-tests, must stay GREEN
python crl_demo.py      # code-review retrieval demo (~85% / 47% input saved)
python bench/run_bench.py   # tool-level savings report (49.6% aggregate measured)
```

CI (`.github/workflows/ci.yml`) runs the full suite on Python 3.9–3.13 on every push.

## Honest scope

Measured = the toolkit's behavior on representative samples (bench/REPORT.md:
49.6% aggregate char reduction across dedup/compress/astrip/trim/grep/mdnorm/
O-1). End-to-end agent-session savings on each target runtime are a separate
verification that runs on that runtime; the behavioral rules are model-agnostic
but their adherence scales with model quality.

## Usage model

`token-savings` is an **always-on discipline** applied to every message:

- **Input** — dedup → compress → safe-mode before reading into context.
- **Output** — fluff-strip + protect `[[KEEP]]` zones; budget length (O-1..O-5).
- **Continuity** — write `RESUME.md` at the END of any turn with open work, and
  parse it first on resume — never "before compaction" (that event is
  unobservable and never fired).
- **Hygiene** — tabs closed, files <300 lines, fresh thread every 8–10 turns.

Load **engineering-discipline** at the start of any non-trivial task; it owns the
lifecycle and delegates all token mechanics here.

## License

MIT — see [LICENSE](LICENSE).
