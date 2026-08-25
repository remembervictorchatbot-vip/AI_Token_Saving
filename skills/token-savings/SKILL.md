---
name: token-savings
description: "Quality-preserving token & credit saving for every message: dedup repeated file reads, compress tool output (bash/JSON/code), markdown-normalize web/RAG content, audit connector tool-surface cost, budget output length, stabilize the prompt prefix. Load when a session is long, context-heavy, or cost-sensitive — or whenever you re-read files, paste large tool output, or fetch web pages."
version: 7.6.0
author: remembervictorchatbot
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tokens, cost, compression, dedup, context, optimization, continuity]
    related_skills: [engineering-discipline]
---

# Token Savings

Spend fewer tokens without losing a single fact the user needs. If a compression
would drop meaning — DON'T compress. Quality wins over savings. Everything here
is provider-agnostic and pure-stdlib Python (3.9+).

## When to use
- Long / context-heavy sessions (repeated file reads, big tool output, web pages).
- Any task where input or output volume is large relative to the actual answer.
- The toolkit is invoked via `toks` (see Toolkit below); the behavioral rules
  apply to every message.

## Quick reference (apply by default)
1. **Stable prefix (top precedence)** — keep stable content (system instructions,
   tool schemas) at the top; variable content at the end. Never rewrite the
   prefix — that breaks prefix caching everywhere.
2. **Protected zones** — wrap the user's literal request/exact data in
   `[[KEEP]]…[[/KEEP]]`; they survive every compression.
3. **Dedup re-reads** — same file/tool-result read again → substitute
   `§ref:HASH§` instead of re-pasting (variable content only, never the prefix).
4. **Multi-surface compression** — bash → trim_bash (ANSI strip, collapse
   repeats, head/tail); grep → top hits + count; JSON → compress_json (drop
   nulls/debug); code → astrip skeleton; &gt;4KB → archive + skeleton.
5. **Safe-mode** — secrets/stack traces → pass through VERBATIM (0% compression);
   errors → keep key lines. Never mangle what would cause hallucinations.
6. **Continuity** — write a durable checkpoint at the end of any turn with
   open work (host-adaptive: `.workbuddy/RESUME.md` here, the harness's durable
   store elsewhere); parse it FIRST on resume. Never re-derive from scratch.
7. **Hygiene** — files &lt;300 lines; fresh thread every 8–10 turns.
8. **JIT** — compress aggressively, expand on demand via the dedup cache.
9. **Loop detection** — same failed action repeating → stop, root-cause first.
10. **Entropy is diagnostic only** — never auto-delete by entropy.

## Output discipline (O-1..O-5)
- **O-1** machine-consumed output → data only (compact JSON or header-once
  table), zero prose; verify JSON parses before emitting.
- **O-2** pick a length budget BEFORE writing: verdict ≤1 line · classification
  ≤3 · chat reply ≤10–15 · summary ≤1 para · analysis ≤30 · report ≤50–70 ·
  code ≤150 lines · data-only = 0 prose.
- **O-3** reasoning scaled to complexity — simple tasks answer directly, never
  narrate thinking.
- **O-4** answer-once: same query + same context already answered this session →
  short pointer + delta. Deterministic facts only; regenerate if inputs changed.
- **O-5** end at the deliverable — no trailing filler/sign-offs.
- **O-6** validate-then-emit: before sending any code/data/markdown run the
  cheapest check that would catch a retry (compiles? parses? fences balanced?).

## Toolkit (portable)
The skill dir is resolved via `$HERMES_SKILL_DIR` automatically, so `toks`
works from any cwd:

```
${HERMES_SKILL_DIR}/bin/toks selftest
${HERMES_SKILL_DIR}/bin/toks dedup --text "$(cat file.txt)"
${HERMES_SKILL_DIR}/bin/toks astrip --text "$CODE" --lang py
${HERMES_SKILL_DIR}/bin/toks compress-json --text '{"a":1,"b":null}'
${HERMES_SKILL_DIR}/bin/toks trim-bash --text "$OUTPUT"
${HERMES_SKILL_DIR}/bin/toks mdnorm --text "$(curl -s URL)" --source html
${HERMES_SKILL_DIR}/bin/toks toolaudit --manifest conns.json
${HERMES_SKILL_DIR}/bin/toks output-budget --task analysis
${HERMES_SKILL_DIR}/bin/toks dedup --diff --text "$(cat file.txt)"   # delta re-read
${HERMES_SKILL_DIR}/bin/toks cost-estimate --steps 12 --ctx-chars 120000   # G1 preflight
${HERMES_SKILL_DIR}/bin/toks surface --path file.py                       # read-me-first
${HERMES_SKILL_DIR}/bin/toks check-syntax --text "$CODE" --lang py        # O-6 gate
${HERMES_SKILL_DIR}/bin/toks audit-session --file transcript.txt          # self-audit
${HERMES_SKILL_DIR}/bin/toks input-gate --text "$(cat tool_output.txt)"   # I-1: context-ready
${HERMES_SKILL_DIR}/bin/toks input-meter --file transcript.txt             # session input cost
${HERMES_SKILL_DIR}/bin/toks output-gate --text "$REPLY" --task analysis   # I-5 before emit
${HERMES_SKILL_DIR}/bin/toks autopilot --file transcript.txt               # I-6 loop
${HERMES_SKILL_DIR}/bin/toks doctor                                         # I-7 wiring check
```

Requires: Python 3.9+ on PATH. No third-party dependencies.

## Pattern reference (absorbed skills, v7.6 consolidation)

Decision rules from merged token skills — mechanisms live in the `toks` CLI:

- **Model-tier routing** (absorbed `software-development/model-tier-routing`):
  route each task to the lowest sufficient tier before dispatch.
  Tier 1 mechanical (format/rename/convert/regex/lint, single-file) →
  cheap model. Tier 2 pattern-matching (code-from-spec, bugfix, tests,
  docs) → standard. Tier 3 reasoning (architecture, security analysis,
  novel debugging, cross-module refactor) → frontier. Preflight:
  `toks route --task "..."`. Cost delta vs uniform-top: ~95% on mechanical.

- **Progressive disclosure** (absorbed
  `software-development/progressive-disclosure-pattern`): keep base prompt
  Layer 1 only — mandates/security/operational rules stay inline; history,
  tables ≥4 rows, enumerations ≥6 bullets, >40-line prose go to reference
  files with a pointer that states rule + trigger + exact path. Security
  content NEVER defers entirely. Target ≤30k tokens. Audit:
  `toks pd --file AGENTS.md`.

- **Sub-agent isolation** (absorbed archived multi-agent-token-optimization):
  children get zero parent history — goal + context + paths + output
  contract only; state updates as deltas. Check: `toks isolate --goal ...`.

- **Re-read suppression / hot-memory decay**: `toks read-cache` (HIT =
  reuse cached ref) and `toks memory-decay --file MEMORY.md` (demote done/
  stale, compress bloat) — the decayed file loads every turn, so audit it
  regularly.

## Verify
- `hermes skills list` shows token-savings.
- `toks selftest` → ALL PASS (225 tests). If a test fails, the install is broken.
