---
name: token-savings
description: THE single, unified, quality-preserving token-saving + prompt-optimization skill for ALL global communications (input context assembly + output generation + code review + continuity). Synthesizes ojuschugh1/sqz (file-hash dedup + safe mode), alexgreensh/token-optimizer (multi-surface compression + compaction-safe lifecycle), vaibkumr/prompt-optimizer (protected zones + entropy-as-diagnostic), the crl code-review engine (diff-aware retrieval), behavioral control (fluff stripping, pre-code clarification, lazy-senior-dev stdlib preference), AST/comment JIT context compression, and context hygiene (close tabs, <300-line files, fresh thread every 8-10 turns). Bundled `toks/` (general) + `crl/` (code-review) toolkits, with a full self-test suite (`python -m toks.cli selftest`). This is the ONE place token-saving logic lives; engineering-discipline and rag-engineering delegate to it. Auto-applied to every message.
agent_created: true
---

# Token Savings — The Unified Skill (single source of truth)

One discipline applied to **every** message: how context is built (input), how
replies are written (output), and how the learning loop survives (continuity).
Goal: spend fewer tokens **without losing a single fact the user needs**. If a
compression would drop meaning → DON'T compress. Quality wins over savings.

## Activation — standing, automatic (no manual step)

This skill is a **default, always-on discipline**. The agent applies Parts A–F to
**every** message without an opt-in. There is exactly one token-saving skill; no
other skill duplicates these rules. `engineering-discipline` and `rag-engineering`
are separate *domains* (lifecycle, RAG) that **reference** this skill for token
mechanics — they contain zero duplicated token rules.

- **Input:** before injecting any file / tool result / URL body, dedup + compress + safe-mode.
- **Output:** fluff-strip, lean structure, protected zones around the user's literals.
- **Continuity:** write a durable checkpoint to `RESUME.md` at the end of every turn where work is open (USE-9). "Before compaction" is unobservable and never fired — the file is what survives.
- **Hygiene:** close tabs, keep files <300 lines, fresh thread every 8–10 turns.

## Scope

| Surface | Covered by |
|---------|------------|
| Input assembly | dedup, multi-surface compression, AST/JIT, safe-mode |
| Output generation | fluff stripping, behavioral control, lean structure |
| Code review | `crl` diff-aware retrieval (folded in from token-efficient-code-review) |
| Continuity | durable `RESUME.md` checkpoint (USE-9) — survives compaction/turn boundaries |
| Hygiene | tab/file/thread discipline |

Out of scope: re-implementing sqz's Rust binary or token-optimizer's hook daemon.
We keep their *logic*, re-implemented as stdlib Python + behavior.

## Quick reference (apply by default)

**USE-0 — Stable prefix (highest precedence, provider-agnostic).** Put stable
content (system instructions, tool schemas, standing rules) at the **top**; put
variable user content at the **end**. No cache-busters (per-turn timestamps,
shuffled examples, random IDs). True for *any* runtime that caches by prefix.
**Outranks Rule 2:** never dedup/rewrite the stable prefix — only dedup the
variable suffix. (Resolves the dedup-vs-cache conflict: rewriting the prefix
breaks caching everywhere.)

1. **Protected zones** — wrap the user's literal request, exact code/data, IDs/paths/constraints in `[[KEEP]]…[[/KEEP]]`. They survive every compression (see `toks/protect.py`).
2. **File-hash dedup (variable suffix only)** — `DedupCache().ref(content)` on re-reads of *variable* content → `§ref:HASH§` (claimed ≈70%+ over long sessions; not independently benchmarked in our env). Never apply to the stable prefix (USE-0).
3. **Multi-surface compression** — bash→`trim_bash`, grep→`summarize_grep`, JSON→`compress_json`, code→`astrip`, >4KB→archive+skeleton.
4. **Durable continuity (USE-9)** — write `RESUME.md` at end of every turn with open work (Decisions · Modified files · Open questions · Next steps · **Lessons to carry**). Not "before compaction" — that event is unobservable.
5. **Safe-mode** — `safemode.risk_level` = `unsafe` (secrets/stack traces) → 0% compression, pass through verbatim; `caution` (errors) → keep key lines; `safe` → full compression.
6. **Behavioral control** — fluff stripping, pre-code clarification interview, lazy-senior-dev stdlib preference, loop/retry detection.
7. **Context hygiene** — close unused tabs, files <300 lines, fresh thread every 8–10 turns.
8. **JIT expansion** — compress aggressively, expand on demand via the dedup/expand cache (or MCP daemon in infra-rich setups). Compressed ≠ lost.
9. **Loop/retry detection** — same failed action repeating → STOP, root-cause first.
10. **Entropy is diagnostic, not a delete button** — use it to find boilerplate to trim; never auto-delete (blind entropy drops accuracy 0.32→0.22 in prompt-optimizer's own eval).

**USE-7 — Tool-surface minimization.** Audit always-on MCP/tool schemas (`toks/toolaudit.py` —
estimates tokens/call per connector, ranks, flags prune candidates). The disconnect itself is a
*user action* (the skill documents how, never auto-disconnects).
**USE-8 — Markdown-first** normalization for web/RAG ingestion — `toks/mdnorm.py` (HTML → clean MD).
**O-1..O-5 — Output economics** (data-only output, length budgets, reasoning scaling,
answer-once caching, end-at-deliverable) — see Part F / `toks/output.py`.
**USE-9 — Session phase-splitting + durable `RESUME.md`** — see Part E.

---

## PART A — Behavioral Control (cut output, prevent re-work)

**A1. Fluff stripping.** Lead with the answer. Delete hedges ("Great question!",
"As an AI…"), meta-commentary, and restated context. One declarative sentence
beats three padded ones.

**A2. Pre-code clarification interview.** Before writing non-trivial code, ask the
few high-leverage questions (language/runtime, exact inputs/outputs, constraints,
edge cases). A 30-token question prevents a 3000-token wrong implementation +
re-work. Clarify → then code.

**A3. Lazy senior-dev, native/stdlib first.** Prefer the language's stdlib over
heavy deps; write the minimum correct code; don't over-abstract. Less code =
fewer tokens to write, read, and debug. If a dep is truly needed, say why.

**A4. Loop / retry detection.** Same failed action repeating → STOP, root-cause
first. Never burn tokens re-attempting blindly.

---

## PART B — Context Compression (claimed 60–90% input reduction)

**B1. AST extraction (`toks/astrip.py`).** For re-reads, send signatures +
imports, drop bodies/comments. `astrip(code)` returns the skeleton; full source is
recoverable via the dedup/expand cache (JIT). Up to ~90% on large modules (claimed).

**B2. Comment / boilerplate stripping.** Strip comments and repeated scaffolding
for compression; keep them in the cache so JIT expansion restores them on demand.

**B3. JIT expansion via local cache / MCP daemon.** Compress aggressively, expand
on demand. The `DedupCache` is the local "daemon": first sight keeps full, repeats
return `§ref:HASH§`, and the original is re-readable (or via an MCP proxy in
infra-rich setups). Compressed output is a summary, never a black hole.

**B4. Multi-surface checklist** (scan before emitting any block):
- bash/tool output → `trim_bash` (ANSI strip, collapse repeats, head/tail)
- search/grep → `summarize_grep` (top hits + count, not full dump)
- JSON/tabular → `compress_json` (drop nulls + debug fields, compact)
- file re-reads → `astrip` skeleton + JIT expand (or `skeleton` fallback)
- large results (>4KB) → archive + skeleton, offer expand
- your verbosity → lean (rule A1)

---

## PART C — Unified Integration (the 3 pillars)

**C1. Deduplication via file-hash caching (biggest win: 70%+ over long sessions).**
Before re-injecting a file / tool result / URL body, `DedupCache().ref(content)`:
`None` → first time, keep full; `§ref:HASH§` → duplicate, substitute the ref.
Kills the #1 waste — re-pasting the same file every turn. The cache persists
across turns in a session.

**C2. Durable continuity (USE-9 — the fix for "compaction loss").** At the end of
every turn where work is open, write the checkpoint to `.workbuddy/RESUME.md` via
`toks/resume.py` — *not* "before compaction" (that event is unobservable, so the
rule never fired). Block: Active task · Decisions · Modified files · Open questions ·
Next steps · **Lessons to carry**. On the next turn, `read_resume()` FIRST and
continue — nothing re-derived from scratch. This is the backbone of the learning loop.

**C3. Safe-mode boundaries (prevent compression-induced hallucinations).**
`safemode.risk_level(text)` classifies `unsafe | caution | safe`.
- `unsafe` (secrets, stack traces) → **0% compression, pass through verbatim**.
  Mangling a redacted secret or truncating a stack trace manufactures hallucinations.
- `caution` (errors) → compress but keep the key lines.
- `safe` → apply full compression.

**C4. Protected Zones (`[[KEEP]]…[[/KEEP]]`) + Quality Gate.** Wrap the user's
literal request, exact code/data, IDs/paths/constraints. `quality_gate` verifies
they survive every compression; on a miss, revert. "Compressed" never means
"lost." Entropy is a *diagnostic* to find safe-to-trim boilerplate, never an
auto-delete (prompt-optimizer's own eval: blind entropy drops accuracy 0.32→0.22).

---

## PART D — Context Hygiene (outperforms manual prompt compression)

- **Close unused tabs / files** before they bloat working context.
- **Keep files under 300 lines** (`toks/hygiene.py` flags >300 → split). Smaller
  files are cheaper to read, review, and reason about.
- **Fresh thread every 8–10 turns** — start a new conversation when the current
  one gets long. A clean thread beats squeezing an overgrown one.
- Apply these *instead of* heroic prompt-compression: hygiene is cheaper and
  preserves more signal.

---

## PART E — Provider-agnostic extensions (USE-0 / USE-7 / USE-8 / USE-9)

These are the v5 additions, validated as **true & working at our layer** and
**provider-agnostic** (no provider-specific pricing/numbers — the principle holds
on any runtime, regardless of which model or API serves the request).

**USE-0 — Stable prefix (top precedence).** Stable content (system instructions,
tool schemas, standing rules like this skill) stays at the top and is never
rewritten. Variable user content goes at the end. Avoid cache-busters: per-turn
timestamps, shuffled examples, random IDs in the prompt body. Any runtime that
caches by prefix will then reuse the cached stable portion. **USE-0 outranks Rule
2:** dedup only touches the variable suffix. (If you dedup the prefix, you mutate
its bytes → cache miss → you pay full price. That was a latent bug in v4.)

**USE-7 — Tool-surface minimization.** Each connected MCP/tool server injects its
schema into every request (~tens of thousands of tokens/call for a rich surface).
Audit the always-on set with `toks/toolaudit.py` (est. tokens/call per connector,
ranked, with prune-candidate flags); disconnect servers you don't use. **The
disconnect is a user action** — the tool audits and recommends only, and never
auto-disconnects. Review candidates: the connected connectors in this environment
(agent-mail, baidu-netdisk, feishu, kdocs, netease-mail, notion) — keep what you
use, disconnect the rest.

**USE-8 — Markdown-first (shipped).** For web/RAG ingestion, normalize raw HTML to
clean Markdown before sending to the model (`toks/mdnorm.py`: strips markup/scripts/
nav/footer chrome, keeps headings/lists/tables/code/links and `[[KEEP]]` zones).
Try `toks mdnorm --text "$(curl -s URL)"` on any fetched page.

**USE-9 — Session phase-splitting + durable RESUME.md (the continuity fix).**
Split discovery / implementation / verification across fresh sessions when a thread
gets long. At the end of every turn with open work, `write_resume(state)` →
`.workbuddy/RESUME.md`. Next turn: `read_resume()` and continue. This replaces the
broken "emit before compaction" rule (compaction is unobservable) with something
that actually fires.

---

## PART F — Output economics (O-1..O-5)

The v6 additions: output-side discipline, validated from the 2026 output-token
techniques through the same layer filter as Parts A–E (only what we control
behaviorally — API params like max_tokens / stop sequences / model routing are
out of our layer and rejected). Behavioral rules, **not independently
benchmarked** in our environment — they follow the same "claimed vs tested"
labeling discipline as the rest of this skill.

**O-1 — Data-only structured output.** When the deliverable is machine-consumed
(extraction, classification, config, data), emit **data only** — compact JSON via
`compress_json`, or a header-once table (`toks/output.py: table_lines`) for
uniform rows. Zero prose. Verify the JSON parses before emitting
(`output.valid_json`) — emit-valid-first kills retry loops (residual of
constrained decoding, which itself is out of our layer).

**O-2 — Output length budgeting.** Pick the ceiling *before writing*, from the
task-type table (`toks/output.py: budget`): verdict ≤1 line · classification ≤3 ·
chat reply ≤10–15 · summary ≤1 paragraph · analysis ≤30 · report ≤50–70 · code
snippet ≤150 lines. Enforce it like a contract.

**O-3 — Reasoning scaled to complexity.** Simple tasks: answer directly, no
reasoning narration. Complex tasks: think, but emit only the conclusion + the
decisive points (concise CoT). Never narrate dead ends, discarded attempts, or
meta-commentary. (The host may hide reasoning — that's its layer; this rule is
about not *emitting* narration we control.)

**O-4 — Answer-once caching (session).** Same query + same context already fully
answered this session → return a short pointer + delta instead of regenerating
(`toks/output.py: AnswerCache`, in-memory). **Staleness guard:** deterministic
facts/boilerplate only; if inputs changed, call with `fresh=True` and regenerate.
Never serve a stale answer for evolving analysis. Mirrors input-side DedupCache,
on the output side.

**O-5 — End at the deliverable.** Stop when the answer is done. No trailing
summaries, sign-offs, restated context, or "let me know if…" filler. (A1 cuts the
head; O-5 cuts the tail.)

**Output budget table (O-2 defaults):**

| Task type | Max output |
|-----------|-----------|
| verdict / single fact | 1 line |
| classification / label | 3 lines |
| chat reply | 10–15 lines |
| summary | 1 paragraph |
| analysis / diagnosis | 30 lines |
| report / plan | 50–70 lines |
| code snippet | 150 lines |
| data-only (machine) | data, zero prose |

---

## Toolkit usage (portable — any cwd, any install location)

The toolkit is location-independent: `bin/toks` resolves the skill dir via
`$TOKS_SKILL_DIR` → `$HERMES_SKILL_DIR` → autodetect (see `toks/boot.py`). No
hardcoded paths — works under WorkBuddy, Hermes Agent, or any harness with
Python 3.9+. Run from anywhere:

```bash
toks selftest        # FULL suite (currently 128 tests) — must stay GREEN
toks demo            # quick self-tests
toks dedup --text "$(cat file.txt)"        # ref or [FIRST TIME]
toks astrip --text "$CODE" --lang py       # signature skeleton
toks safemode --text "$TEXT"               # unsafe|caution|safe
toks hygiene --path file.py                # >300 lines? split?
toks compress-json --text '{"a":1,"b":null}'
toks trim-bash --text "$OUTPUT" --max-lines 40
toks summarize-grep --text "$GREP" --top 10
toks protect --text "..." --mode code|json|text   # guarantees [[KEEP]] survives
toks quality-gate --before "..." --after "..."
toks checkpoint --emit --active-task "..." --decisions "d1|d2" --open-questions "q1|q2" --lessons "l1"
toks mdnorm --text "$HTML" --source html   # HTML -> clean Markdown (USE-8)
toks mdnorm --text "$MD" --source md       # normalize messy Markdown
toks toolaudit --manifest conns.json --keep "feishu|notion"   # audit tool surface, recommend-only (USE-7)
toks output-budget --task analysis         # O-2 ceiling in lines
toks output-json --text '{"a":1'           # O-1 gate: VALID / INVALID
toks output-table --header "id|name" --rows "1|Alice;2|Bob"   # O-1 header-once table
toks --help  # resume helper is a library: `from toks import resume; resume.write_resume(state)` / `resume.read_resume()`
```

`bin/toks` runs from any cwd. If `bin/` isn't on PATH, use `bin/toks <cmd>` from
the skill root, or `TOKS_SKILL_DIR=/path bin/toks <cmd>`. The older
`python -m toks.cli <cmd>` form still works from `scripts/` directly.

The full suite (dedup, compress, astrip, safemode, hygiene, quality_gate,
checkpoint, protect, cross-scenario consistency, edge cases, crl smoke) lives in
`scripts/tests/` and runs via `python -m toks.cli selftest`. It is the acceptance
gate: any change to this skill must keep `selftest` GREEN.

### Code review path (folded `crl` engine — was token-efficient-code-review)
```bash
python -m crl.cli index <repo>                            # index once, cached
python -m crl.cli review <repo> --changed app/utils.py --mode function --show
python -m crl.cli summary <repo> --files module.txt --top 12   # cheap tier
python crl_demo.py                                        # token-savings table
```
Index once → retrieve only the changed closure (module or symbol-level) → optional
deterministic pre-flight (ruff/mypy/semgrep/vba-lint) → LLM review on the trimmed
context. Function-mode hits ~85% input saved on leaf changes (measured in crl demo); the deterministic
pre-filter closes coverage gaps the cheap path would miss.

You don't need the toolkit for small cases — apply Parts A–D directly in reasoning.

---

## Integration with the global loop

This is the **single** token-saving module. There is no other skill that owns
token/prompt-optimization logic — `engineering-discipline` and `rag-engineering`
delegate to it and must not duplicate its rules.

- **engineering-discipline** (lifecycle + checkpoint + LESSONS.md carry-over):
  owns the *process*; calls this skill's `toks/checkpoint.py` for continuity and
  applies these rules inside every `study→synthesize→test→monitor→enhance→fix→confirm`
  step. Every checkpoint carries a "Lessons to carry" line so the loop compounds
  and survives compaction.
- **rag-engineering** (retrieval playbook): when the task is retrieval-augmented,
  applies this skill's `astrip`/`compress_json`/`safemode` to retrieved context and
  uses the folded `crl` engine here for codebase retrieval.
- **token-efficient-code-review**: consolidated pointer — its `crl` engine now
  lives in `scripts/crl/` here. No separate token-saving skill remains.
