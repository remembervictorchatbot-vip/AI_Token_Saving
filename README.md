<div align="center">

# AI Token Saving 🪐

<img src="docs/planet-logo.svg" alt="little lovely planet" width="160">

**little lovely planet** — quality-preserving token & credit savings for AI agents

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![CI](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/ci.yml/badge.svg)](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/ci.yml)
[![CodeQL](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/codeql.yml/badge.svg)](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/codeql.yml)
[![Dependencies: zero](https://img.shields.io/badge/dependencies-zero-orange.svg)](skills/token-savings/scripts/toks)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Context is expensive. Re-pasted files, verbose tool output, and padded replies
burn tokens and credits on every message. This project cuts that waste **without
dropping a single fact the user needs** — with a pure-stdlib toolkit and a set of
behavioral rules that work on any model and any harness.

</div>

---

## Quick start ⚡

```bash
# 1. Install (WorkBuddy — user-level, applies to all communications)
cp -R skills/* ~/.workbuddy/skills/

# 2. Verify — 131 tests, must all pass (bin/toks works from any cwd)
toks selftest

# 3. Try it — the same file read twice; the second read collapses to a reference
toks dedup --text "$(cat file.txt)"   # [FIRST TIME — keep full content]
toks dedup --text "$(cat file.txt)"   # §ref:9f86d081...  (≈98% fewer tokens)
```

Also works on [Hermes Agent](dist/hermes/token-savings) and any harness that can
run Python 3.9+ — see [Targets & install](#targets--install).

## Why 🧠

Every agent request carries overhead: repeated file reads, raw HTML, ANSI-laden
logs, reams of JSON with nulls and debug fields, and output prose nobody asked
for. Token costs scale with that waste — and so do credits, latency, and context
limits. The fix is a discipline, not a single trick:

- **Never re-paste what you already read** (dedup)
- **Never send markup when meaning is enough** (compress / normalize)
- **Never generate prose when data will do** (output discipline)
- **Never lose the one fact that mattered** (protected zones)

## What it does ✨

| Surface | Tool | Effect |
|---|---|---|
| Repeated file/tool reads | `toks dedup` | second read → `§ref:HASH§` (measured 98.3%) |
| JSON payloads | `toks compress-json` | drops nulls/debug fields, compacts (43.0%) |
| Code re-reads | `toks astrip` | signatures/imports only, bodies recoverable (79.2%) |
| Build logs / shell output | `toks trim-bash` | ANSI strip, collapse repeats, head/tail (75.1%) |
| Web / RAG ingestion | `toks mdnorm` | HTML → clean Markdown, chrome stripped (28.4%) |
| Connector tool surface | `toks toolaudit` | est. tokens/call per connector, recommend-only |
| Output generation | `toks output-*` | length budgets, JSON gate, header-once tables (O-1..O-5) |
| Secrets & stack traces | `toks safemode` | **0% compression — pass through verbatim** |
| Session continuity | `RESUME.md` | checkpoint survives context loss, never re-derives |

**Before / after — output discipline (O-1):**

```
Without (verbose prose, ~45 tokens):
  "The email address is support@acme.com and the date appears to be 2026-03-14."

With (data-only, ~25 tokens):
  {"email": "support@acme.com", "date": "2026-03-14"}
```

## Measured impact 📊

Deterministic, stdlib-only benchmark ([bench/REPORT.md](bench/REPORT.md)) on
representative samples:

| Surface | Sample | Before | After | Saved |
|---|---|---|---|---|
| dedup | config re-read (2nd read) | 1,059 chars | 18 | **98.3%** |
| summarize-grep | 150 hits | 4,449 | 334 | **92.5%** |
| astrip | ~150-line module | 6,816 | 1,420 | **79.2%** |
| trim-bash | build log w/ ANSI | 3,519 | 877 | **75.1%** |
| O-1 data-only | chat reply → table | 345 | 98 | **71.6%** |
| compress-json | 500-item payload | 37,293 | 21,243 | **43.0%** |
| mdnorm | 120-paragraph docs page | 14,118 | 10,109 | **28.4%** |
| **Aggregate** | | **67,599** | **34,099** | **49.6%** |

_Honest scope: these are tool-level measurements. End-to-end savings on a live
agent session also depend on the model following the behavioral rules — a
frontier model complies better than a small local one. No inflated claims._

## How it works ⚙️

```
 input (files / tool output / web pages / re-reads)
   │
   ▼
 ┌────────────────────────────────────────────────┐
 │ dedup · compress_json · trim_bash · astrip    │
 │ mdnorm (HTML→MD) · summarize_grep             │
 │ safemode: secrets & stack traces pass VERBATIM│
 └────────────────────────────────────────────────┘
   │  [[KEEP]] zones survive every compression
   ▼
 model  (stable prefix first — never rewritten, USE-0)
   │
   ▼
 ┌────────────────────────────────────────────────┐
 │ O-1 data-only output   O-2 length budgets     │
 │ O-3 reasoning scaled   O-4 answer-once cache  │
 │ O-5 end at the deliverable                    │
 └────────────────────────────────────────────────┘
   │
   ▼
 lean answer — nothing the user needed is lost
```

## Targets & install 🎯

| Target | Status | Install |
|---|---|---|
| **WorkBuddy** | native · 131/131 tests · gated releases | `cp -R skills/* ~/.workbuddy/skills/` |
| **Hermes Agent** | verified (installs, registers, enabled) | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Codex / Claude Code / OpenCode-style** | behavioral rules port; needs skill conversion | copy `skills/token-savings`, Python 3.9+ on PATH |
| **Harness w/o skill loader** (custom DeepSeek harness, AI Studio, local agents) | system-prompt transplant + context filter | inject `dist/system-prompt/token-savings-prompt.md`; run `dist/deepseek-harness/toks_filter.py` in front of your model endpoint |
| **DeepSeek-style harness** (OpenAI-compatible: DeepSeek API, LM Studio, Qwen Code, OpenCode) | dedicated adapter — context filter + prompt bundle | see [dist/deepseek-harness/README.md](dist/deepseek-harness/README.md) |
| Ollama / LM Studio (model servers) | no agent loop — condensed prompt applies | same system-prompt bundle |

The toolkit is location-independent: `bin/toks` resolves its own skill dir via
`$TOKS_SKILL_DIR` → `$HERMES_SKILL_DIR` → autodetect. No hardcoded paths, no
installation, no dependencies.

> `dist/hermes/token-savings/scripts/` is a **generated bundle** (copy of
> `skills/token-savings/scripts/`) so the Hermes skill stays self-contained.
> The source of truth is `skills/`.

## Usage model 🔁

`token-savings` is an **always-on discipline**, not a one-shot script:

- **Input** — dedup → compress → safe-mode before anything enters context.
- **Output** — fluff-strip, protect `[[KEEP]]` zones, budget length (O-1..O-5).
- **Continuity** — write `RESUME.md` at the END of any turn with open work; parse
  it first on resume. Never "before compaction" (that event is unobservable).
- **Hygiene** — files <300 lines; fresh thread every 8–10 turns.

Pair it with **engineering-discipline** (the mandatory phase-gate SOP) and
**rag-engineering** for retrieval work — both delegate all token mechanics here.

## Design principles 🧬

Synthesized from three open-source approaches — logic kept, heavy dependencies
rejected:

| Source | Kept (portable logic) | Rejected |
|---|---|---|
| **ojuschugh1/sqz** | content-hash dedup, lossless pipeline, entropy safe-mode | Rust binary |
| **alexgreensh/token-optimizer** | multi-surface compression, checkpoint, quality gate, loop detection | hook daemon, SQLite dashboard |
| **vaibkumr/prompt-optimizer** | protected zones `[[KEEP]]`, entropy as *diagnostic* | blind entropy delete (drops accuracy) |

## FAQ 💡

**Does it really save tokens?**
Yes, measurably at the tool level — 49.6% aggregate on representative samples
(see [Measured impact](#measured-impact)). Agent-level savings scale with how
well the model follows the rules. No magic numbers, everything is reproducible
via `python bench/run_bench.py`.

**Will it work with my model / harness?**
The rules are model-agnostic. The toolkit is pure stdlib Python 3.9+ — it runs
anywhere Python runs. Native skills for WorkBuddy and Hermes; a condensed
system-prompt bundle for everything else.

**Does it send my data anywhere?**
No. Zero telemetry, zero network calls, zero third-party dependencies. Everything
runs locally and in-process.

**Why not LLMLingua / Outlines / vLLM?**
Those are powerful but heavyweight (torch, native serving stacks) and live at the
API/serving layer this project deliberately doesn't control. This toolkit
achieves the same *discipline* with a pure-stdlib, portable, testable core.

## Community 🤝

[Contributing](CONTRIBUTING.md) · [Code of Conduct](CODE_OF_CONDUCT.md) ·
[Security policy](SECURITY.md)

## License

MIT — see [LICENSE](LICENSE). Not affiliated with, endorsed by, or connected to
any product or platform named in the compatibility matrix.

---

<div align="center">
  <em>made with ♥ on a little lovely planet 🌍</em>
</div>
