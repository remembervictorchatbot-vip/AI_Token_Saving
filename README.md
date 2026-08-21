<div align="center">

# AI Token Saving 🪐

<img src="docs/planet-logo.svg" alt="little lovely planet" width="160">

**little lovely planet** — quality-preserving token & credit savings for AI agents

**Model-agnostic · harness-agnostic · pure stdlib Python 3.9+ · zero dependencies · zero telemetry**

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

## Quick start ⚡ — works with any model, any harness

**Universal path — no install, works everywhere** (any harness with a system
prompt and a model endpoint — WorkBuddy, Claude Code, Codex, OpenCode, Qwen
Code, custom DeepSeek harnesses, AI Studio, local agents…):

```bash
# 1. Behavioral rules — paste dist/system-prompt/token-savings-prompt.md
#    at the TOP of your system prompt (fluff-strip, budgets, dedup, continuity).

# 2. Context filter — compress requests before they reach the model
#    (stdlib Python 3.9+, OpenAI-compatible endpoint):
TOKS_UPSTREAM=https://api.deepseek.com/v1 python3 dist/deepseek-harness/toks_filter.py
#    then point your harness's base_url at http://127.0.0.1:8090/v1
#    (LM Studio / llama.cpp: TOKS_UPSTREAM=http://localhost:1234/v1)

# 3. Optional — portable CLI on PATH (verify, then use directly):
export PATH="$PWD/skills/token-savings/bin:$PATH"
toks selftest        # 179 tests, all must pass
```

**Native one-command installs** (best on these platforms):

| Platform | Install |
|---|---|
| **WorkBuddy** | `cp -R skills/* ~/.workbuddy/skills/` |
| **Hermes Agent** | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Claude Code / Codex / OpenCode-style** | copy `skills/token-savings`, ensure Python 3.9+ on PATH (behavioral rules port) |
| **Anything else** | universal path above — it always works |

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
| Near-repeat re-reads (v8) | `toks dedup --diff` | delta hunks only — unchanged parts stay cached (77.4%) |
| Input cost preflight (v8) | `toks cost-estimate` | estimate spend BEFORE a task (steps × ctx, peak/idle) |
| Read-me-first (v8) | `toks surface` | one line per symbol with line numbers — py/json/md/conf |
| Output validation (v8) | `toks check-syntax` | O-6 gate: catch retries before emitting |
| Session self-audit (v8) | `toks audit-session` | flags re-reads, prose bloat, loops, bad JSON |
| Automatic input gate (v9) | `toks input-gate` | context-ready content: dedup → compress → protect → fidelity marker (71.5%) |
| Session input meter (v9) | `toks input-meter` | actual input cost + recoverable repeat waste |
| Fidelity facts (v9) | `toks quality-gate --facts` | I-4: key facts survive lossy steps |

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
| dedup --diff (v8) | config re-read after edit | 1,067 chars | 241 | **77.4%** |
| input-gate (v9) | 200-item payload w/ protected zone | 7,585 chars | 2,160 | **71.5%** |
| summarize-grep | 150 hits | 4,449 | 334 | **92.5%** |
| astrip | ~150-line module | 6,816 | 1,420 | **79.2%** |
| trim-bash | build log w/ ANSI | 3,519 | 877 | **75.1%** |
| O-1 data-only | chat reply → table | 345 | 98 | **71.6%** |
| compress-json | 500-item payload | 37,293 | 21,243 | **43.0%** |
| mdnorm | 120-paragraph docs page | 14,118 | 10,109 | **28.4%** |
| **Aggregate** | | **76,251** | **36,500** | **52.1%** |

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
| **Any harness w/ a model endpoint** (universal) | behavioral rules + context filter — always works | system-prompt bundle + `toks_filter.py` (see [Quick start](#quick-start--works-with-any-model-any-harness)) |
| **DeepSeek-style harness** (DeepSeek API, LM Studio, Qwen Code, OpenCode) | dedicated adapter — context filter + prompt bundle | see [dist/deepseek-harness/README.md](dist/deepseek-harness/README.md) |
| **WorkBuddy** | native · 179/179 tests · gated releases | `cp -R skills/* ~/.workbuddy/skills/` |
| **Hermes Agent** | verified (installs, registers, enabled) | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Codex / Claude Code / OpenCode-style** | behavioral rules port; needs skill conversion | copy `skills/token-savings`, Python 3.9+ on PATH |
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
Yes, measurably at the tool level — 52.1% aggregate on representative samples
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

## Documentation 📚

- [docs/](docs/) — index: **Obsidian study vault** (`docs/obsidian/`)
  and **GitHub wiki staging** (`docs/wiki/`) with full architecture, CLI
  reference, benchmark, skills, and glossary notes.
- [DeepSeek-harness adapter](dist/deepseek-harness/README.md) — wiring guide
  for the context filter.

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
