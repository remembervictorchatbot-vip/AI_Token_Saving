<div align="center">

# AI Token Saving 🪐

<img src="docs/planet-logo.svg" alt="little lovely planet" width="160">

**little lovely planet** — quality-preserving token & credit savings for AI agents

**Model-agnostic · harness-agnostic · pure stdlib Python 3.9+ · zero dependencies · zero telemetry**

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Tests: 276](https://img.shields.io/badge/tests-276-green.svg)](skills/token-savings/scripts/tests)
[![CI](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/ci.yml/badge.svg)](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/ci.yml)
[![CodeQL](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/codeql.yml/badge.svg)](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/actions/workflows/codeql.yml)
[![Dependencies: zero](https://img.shields.io/badge/dependencies-zero-orange.svg)](skills/token-savings/scripts/toks)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Context is expensive. Re-pasted files, verbose tool output, and padded replies
burn tokens and credits on every message. This project cuts that waste
**all-round — input, output, and flow — without dropping a single fact the
user needs**: a pure-stdlib toolkit, a set of standing rules, and a
self-enforcing autopilot loop that audits and corrects itself.

</div>

---

## Quick start ⚡ — auto-start for any model, any harness

**One-time apply (2 minutes, then it runs on its own):**

```bash
# 1. Portable CLI + autopilot wiring (prints the exact lines for your shell):
skills/token-savings/bin/toks setup            # -> copy-paste into ~/.bashrc / ~/.zshrc
toks setup --write-env                          # optional: .toks.env template for the filter
toks doctor                                     # verify: all checks OK = autopilot wired

# 2. Behavioral rules — paste dist/system-prompt/token-savings-prompt.md
#    at the TOP of your system prompt (18 rules; auto-start for any model).

# 3. Optional automatic endpoint compression — every request passes the input
#    gate at the wire, zero model compliance needed (OpenAI-compatible endpoints):
TOKS_UPSTREAM=https://api.deepseek.com/v1 python3 dist/deepseek-harness/toks_filter.py
#    then point your harness base_url at http://127.0.0.1:8090/v1
#    (LM Studio / llama.cpp: TOKS_UPSTREAM=http://localhost:1234/v1)

# 4. Self-test:
toks selftest        # 276 tests, all must pass
```

**Native one-command installs** (best on these platforms):

| Platform | Install |
|---|---|
| **WorkBuddy** | `cp -R skills/* ~/.workbuddy/skills/` (skill auto-loads, applies to every message) |
| **Hermes Agent** | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Any MCP host** | register `dist/mcp/toks_mcp_server.py` (see [dist/mcp/README.md](dist/mcp/README.md)) — 5 tools, ~127 tok |

| **Claude Code / Codex / OpenCode-style** | copy `skills/token-savings`, Python 3.9+ on PATH + the system-prompt bundle |
| **Anything else** | `toks setup` + the system-prompt bundle — always works |

## One command to manage it all 🤖

```bash
toks auto            # full sweep: wiring check + live MCP discovery +
                     # tool-surface audit + skills audit → prioritized fixes
```

Tools and skills are managed by the toolkit itself — no manual manifests:

| Layer | Command | What you get |
|---|---|---|
| Tools | `toks discover --live` | real MCP handshake → exact tool schemas per connector (estimate fallback) |
| Tools | `toks toolaudit` / `tool-search` | cost audit, prune candidates, Claude-style defer-loading index + BM25 search |
| Skills | `toks skills-audit` / `skills-index` | near-dup / vague-trigger / oversized / stale detection; one-line discovery index |
| Safety | `toks retrieve <hash>` | every compression is reversible — verbatim originals cached locally |

## Why 🧠

Every agent request carries overhead: repeated file reads, raw HTML, ANSI-laden
logs, reams of JSON with nulls and debug fields, and output prose nobody asked
for. Token costs scale with that waste — and so do credits, latency, and context
limits. The fix is a discipline with **three layers**, not a single trick:

- **Input** — nothing crosses into context un-gated (dedup → compress → safe-mode → protect)
- **Output** — nothing is emitted un-checked (budget, validity, filler)
- **Flow** — nothing re-derived, nothing repeated (continuity, hygiene, loop detection)
- **Quality** — compressed never means lost: `[[KEEP]]` zones, safe-mode, and fact checks are mechanical guarantees

## What it does ✨ (39 commands)

| Surface | Tool | Effect |
|---|---|---|
| **Automatic input gate (v9)** | `toks input-gate` | context-ready content: idempotency → safe-mode → dedup → tiered compress → protect (71.5%) |
| Endpoint auto-compression | `toks_filter.py` | every request gated at the wire, zero model compliance (proxy) |
| Near-repeat re-reads (v8) | `toks dedup --diff` | delta hunks only — unchanged parts stay cached (77.4%) |
| Repeated file/tool reads | `toks dedup` | second read → short ref (98.3%) |
| JSON payloads | `toks compress-json` | drops nulls/debug fields, compacts (43.0%) |
| Code re-reads | `toks astrip` | signatures/imports only, bodies recoverable (79.2%) |
| Build logs / shell output | `toks trim-bash` | ANSI strip, collapse repeats, head/tail (75.1%) |
| Web / RAG ingestion | `toks mdnorm` | HTML → clean Markdown, chrome stripped (28.4%) |
| Read-me-first (v8) | `toks surface` | one line per symbol with line numbers — py/json/md/conf |
| Connector tool surface | `toks toolaudit` | est. tokens/call per connector, recommend-only |
| **Output gate (v10)** | `toks output-gate` | O-1..O-6 checks on a reply BEFORE it is sent |
| Output generation | `toks output-*` | length budgets, JSON gate, header-once tables (O-1..O-5) |
| Validate-then-emit (v8) | `toks check-syntax` | O-6: catch retries before emitting |
| **Session autopilot (v10)** | `toks autopilot` | meter + audit + gate → NEXT-TURN DIRECTIVES |
| **Environment doctor (v10)** | `toks doctor` | is auto-saving actually wired here? one-liner fixes |
| **One-time setup (v10)** | `toks setup` | prints the exact shell/endpoint wiring for this machine |
| Session self-audit (v8) | `toks audit-session` | flags re-reads, prose bloat, loops, bad JSON |
| Session input meter (v9) | `toks input-meter` | actual input cost + recoverable repeat waste |
| Cost preflight (v8) | `toks cost-estimate` | estimate spend BEFORE a task (steps × ctx, peak/idle) |
| Secrets & stack traces | `toks safemode` | **0% compression — pass through verbatim** |
| Fidelity facts (v9) | `toks quality-gate --facts` | key facts survive lossy steps |
| Session continuity | `RESUME.md` | checkpoint survives context loss, never re-derives |
| Auto-checkpoint (v10) | `toks checkpoint --auto` | extracts open work heuristically — one call |
| **Prompt layer audit (v11)** | `toks pd` | progressive-disclosure: Layer1/Layer2 sections, extraction plan, ≤30k budget |
| **Tier routing (v11)** | `toks route` | mechanical/pattern/reasoning preflight + cost delta vs uniform top tier (95% on mechanical) |
| Sub-agent isolation (v11) | `toks isolate` | leak-free child briefs; flags history-leaks & >2k state dumps |
| **Re-read suppression (v11)** | `toks read-cache` | mtime+hash HIT → skip re-read, reuse cached ref |
| **Memory decay (v11)** | `toks memory-decay` | hot-memory audit: demote done/stale, compress bloat — cuts every-turn context |
| **Smart auto-compress (v11c)** | `toks auto-compress` | ratio threshold 0.3 min / 0.5 enforce: APPLY ≥50%, SHADOW report-only in 30–50% band, SKIP below or on secrets (LLMLingua + Claude-compaction + LeanCTX synthesis) |
| **Tool-search surface (v11d)** | `toks tool-search` | Claude Tool-Search pattern for any harness: name+desc index (~30 tok/tool), defer_loading plan, lite-BM25 query |
| **Live MCP discovery (v12)** | `toks discover --live` | real MCP handshake (initialize→tools/list): exact tool names/schemas, estimate fallback |
| **Skills management (v12b)** | `toks skills-audit` / `skills-index` | near-dup/vague/oversized/stale audit + Layer-1 discovery index with BM25 search |
| **One-command full-auto (v13)** | `toks auto` | doctor + live discovery + toolaudit + skills-audit → prioritized directives — the whole discipline in one invocation |
| **Reversible compression (v14)** | `toks retrieve <hash>` | CCR: verbatim originals cached on every compress (`[ccr:hash]` markers); lossy-but-recoverable, never destructive |
| **MCP adapter (v15)** | `dist/mcp/toks_mcp_server.py` | 5-tool stdio MCP server (~127 tok) — any MCP host gets the discipline without shell access ([README](dist/mcp/README.md)) |

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
| dedup --diff (v8) | config re-read after edit | 1,067 chars | 241 | **77.4%** |
| trim-bash | build log w/ ANSI | 3,519 | 877 | **75.1%** |
| input-gate (v9) | 200-item payload w/ protected zone | 7,585 chars | 2,160 | **71.5%** |
| O-1 data-only | chat reply → table | 345 | 98 | **71.6%** |
| compress-json | 500-item payload | 37,293 | 21,243 | **43.0%** |
| mdnorm | 120-paragraph docs page | 14,118 | 10,109 | **28.4%** |
| **Aggregate** | | **76,251** | **36,500** | **52.1%** |

_Honest scope: these are tool-level measurements. End-to-end savings on a live
agent session also depend on the model following the behavioral rules — a
frontier model complies better than a small local one. The autopilot loop
(audit → directives → apply) exists precisely to raise that compliance. No
inflated claims._

## How it works ⚙️ — the self-enforcing loop

```
 input (files / tool output / web pages / re-reads)
   |
   ▼
 ┌────────────────────────────────────────────────┐
 │ INPUT GATE (v9) - automatic at the wire:       │
 │ idempotency · safemode · dedup · tiered compress│
 │ protect [[KEEP]] · fidelity marker             │
 └────────────────────────────────────────────────┘
   |  secrets & stack traces pass VERBATIM (0%)
   ▼
 model  (stable prefix first — never rewritten, USE-0)
   |
   ▼
 ┌────────────────────────────────────────────────┐
 │ OUTPUT GATE (v10) - before emit:              │
 │ O-1 data-only · O-2 budget · O-3 reasoning     │
 │ O-4 answer-once · O-5 end at deliverable       │
 │ O-6 validate-then-emit                        │
 └────────────────────────────────────────────────┘
   |
   ▼
 lean answer — nothing the user needed is lost

 ┌────────────────────────────────────────────────┐
 │ AUTOPILOT (v10) - every ~10 turns:            │
 │ input-meter → audit-session → output-gate      │
 │ → NEXT-TURN DIRECTIVES (read first, apply)     │
 │ doctor checks the wiring · checkpoint --auto   │
 └────────────────────────────────────────────────┘
```

## Targets & install 🎯

| Target | Status | Install |
|---|---|---|
| **Any harness w/ a model endpoint** (universal) | behavioral rules + context filter — always works | `toks setup` + system-prompt bundle + `toks_filter.py` (see [Quick start](#quick-start--auto-start-for-any-model-any-harness)) |
| **DeepSeek-style harness** (DeepSeek API, LM Studio, Qwen Code, OpenCode) | dedicated adapter — context filter + prompt bundle | see [dist/deepseek-harness/README.md](dist/deepseek-harness/README.md) |
| **WorkBuddy** | native · 276/276 tests · gated releases | `cp -R skills/* ~/.workbuddy/skills/` |
| **Hermes Agent** | verified (installs, registers, enabled) | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Codex / Claude Code / OpenCode-style** | behavioral rules port; needs skill conversion | copy `skills/token-savings`, Python 3.9+ on PATH |
| Ollama / LM Studio (model servers) | no agent loop — condensed prompt applies | same system-prompt bundle |

The toolkit is location-independent: `bin/toks` resolves its own skill dir via
`$TOKS_SKILL_DIR` → `$HERMES_SKILL_DIR` → autodetect, and preserves the caller's
cwd for relative `--path`/`--file` args. No hardcoded paths, no installation,
no dependencies. After wiring, `toks doctor` confirms every layer is live.

> `dist/hermes/token-savings/scripts/` is a **generated bundle** (copy of
> `skills/token-savings/scripts/`). The source of truth is `skills/`.

## Usage model 🔁

`token-savings` is an **always-on discipline**, not a one-shot script:

- **Input** — dedup → compress → safe-mode → protect before anything enters context.
- **Output** — fluff-strip, protect `[[KEEP]]` zones, budget length (O-1..O-6).
- **Continuity** — write `RESUME.md` at the END of any turn with open work; parse
  it first on resume (`toks checkpoint --auto` makes this one call).
- **Self-correction** — run `toks autopilot` every ~10 turns; apply its directives.
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
well the model follows the rules; the autopilot loop exists to raise exactly that.
Reproduce everything via `python bench/run_bench.py`.

**How do I make it fully automatic?**
Three layers, each verified by `toks doctor`: (1) `toks setup` wires the CLI,
(2) the system-prompt bundle auto-starts the rules in any model, (3) `toks_filter.py`
gates every request at the endpoint — zero model compliance needed.

**Will it work with my model / harness?**
The rules are model-agnostic. The toolkit is pure stdlib Python 3.9+ — it runs
anywhere Python runs. Native skills for WorkBuddy and Hermes; a condensed
system-prompt bundle for everything else.

**Does it send my data anywhere?**
No. Zero telemetry, zero network calls, zero third-party dependencies. Everything
runs locally and in-process.

**Why not LLMLingua / Outlines / vLLM?**
Those are powerful but heavyweight (torch, native serving stacks) and live at the
API/serving layer this project deliberately doesn't control. This toolkit achieves
the same discipline with a pure-stdlib, portable, testable core.

**How do I know the install works?**
`toks selftest` runs 276 tests and must stay GREEN (CI enforces this on Python
3.9–3.13). `toks doctor` checks python/toolkit/filter/PATH and prints the exact
fix for each warning.

## Documentation 📚

- [docs/](docs/) — **Obsidian study vault** (`docs/obsidian/`) + **GitHub wiki
  staging** (`docs/wiki/`) with architecture, CLI reference, benchmark, skills,
  glossary, and changelog notes.
- [DeepSeek-harness adapter](dist/deepseek-harness/README.md) — wiring guide for
  the context filter.

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