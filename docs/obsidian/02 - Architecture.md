---
tags: [token-savings]
---

# 02 - Architecture

How the discipline is applied on every message: context is built (input),
replies are written (output), and the learning loop survives (continuity).

## Pipeline

```
 input (files / tool output / web pages / re-reads)
   |
   v
 +------------------------------------------------+
 | dedup - compress_json - trim_bash - astrip     |
 | mdnorm (HTML->MD) - summarize_grep             |
 | safemode: secrets & stack traces pass VERBATIM |
 +------------------------------------------------+
   |  protected zones survive every compression
   v
 model  (stable prefix first - never rewritten, USE-0)
   |
   v
 +------------------------------------------------+
 | O-1 data-only output   O-2 length budgets      |
 | O-3 reasoning scaled   O-4 answer-once cache   |
 | O-5 end at the deliverable                     |
 +------------------------------------------------+
   |
   v
 lean answer - nothing the user needed is lost
```

## Input side (Parts A-C)

- **Protected zones**: user literals (exact code/data/IDs/paths/constraints)
  are wrapped so they survive every compression; a quality gate verifies on
  every pass and reverts on a miss.
- **Dedup (file-hash)**: re-reads of variable content return a short ref
  instead of the full bytes; first sight keeps the full copy (JIT-expandable).
- **Multi-surface compression**: bash -> trim_bash (ANSI strip, collapse
  repeats, head/tail); grep -> summarize_grep (top hits + count); JSON ->
  compress_json (drop nulls/debug fields, compact); code -> astrip
  (signatures/imports only, bodies recoverable); >4KB -> archive + skeleton.
- **Safe-mode**: risk_level classifies unsafe | caution | safe. Secrets and
  stack traces = unsafe = 0% compression, pass through verbatim (mangling
  them manufactures hallucinations).
- **Stable prefix (USE-0)**: system instructions / tool schemas / standing
  rules stay byte-identical at the top; variable content goes at the end.
  Never rewrite the prefix (rewriting breaks prefix caching on any runtime).

## Output side (Part F, O-1..O-5)

| Rule | What it does |
|---|---|
| O-1 | Data-only when machine-consumed: compact JSON or header-once table, zero prose; verify JSON parses before emitting |
| O-2 | Length budget picked BEFORE writing: verdict <=1 line, classification <=3, chat reply 10-15, summary 1 paragraph, analysis 30, report 50-70, code <=150 lines |
| O-3 | Reasoning scaled to complexity: answer directly for simple tasks; conclusion + decisive points only for complex ones |
| O-4 | Answer-once session cache: same query + context -> short pointer + delta; staleness guard for evolving analysis |
| O-5 | End at the deliverable: no trailing summaries, sign-offs, or filler |
| O-6 (v8) | Validate-then-emit: run the cheapest check that would catch a retry before sending any artifact |

## Continuity (USE-9) & hygiene

- Write a durable checkpoint (RESUME.md) at the END of any turn with open
  work: active task - decisions - modified files - open questions - next
  steps - lessons to carry. Read it FIRST on the next turn. Never re-derive
  from scratch. ('Before compaction' is unobservable and never fired.)
  **Host-adaptive (v8)**: the location follows the harness - .workbuddy/RESUME.md
  under WorkBuddy, the harness task/goal store elsewhere. The rule is the
  observable end-of-turn trigger, not the path.
- Hygiene: close unused tabs, keep files <300 lines, fresh thread every
  8-10 turns.
- Loop detection: same failed action repeating -> STOP, root-cause first.

## Step-cost model (v8, Part G)

Every step re-sends the whole context from prefix cache: spend scales with
steps x context. Estimate BEFORE a task (toks cost-estimate), batch work into
fewer steps, and prefer structural savings (toks surface read-me-first,
toks dedup --diff delta re-read - measured 77.4%) over cleverer compression.

## Tool-surface minimization (USE-7)

Always-on MCP/tool schemas are injected into every request. toolaudit
estimates tokens/call per connector, ranks them, and flags prune candidates.
The disconnect itself is a USER action - the tool only audits and recommends.

## Markdown-first (USE-8)

Web/RAG ingestion normalizes raw HTML to clean Markdown (mdnorm) before the
model sees it: strips markup/scripts/nav/footer chrome, keeps headings/lists/
tables/code/links and protected zones.

See also: [[03 - CLI Reference]] for the concrete commands behind each rule,
and [[07 - Design Principles]] for where these rules came from.