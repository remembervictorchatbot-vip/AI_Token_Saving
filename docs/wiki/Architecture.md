# Architecture

One discipline applied to every message: context is built (input), replies
are written (output), and the learning loop survives (continuity).

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

## Input side

- **Protected zones** - user literals survive every compression; quality
  gate verifies on every pass, reverts on a miss.
- **Dedup (file-hash)** - re-reads return a short ref; first sight keeps
  the full copy (JIT-expandable).
- **Multi-surface compression** - bash -> trim_bash, grep -> summarize_grep,
  JSON -> compress_json, code -> astrip (signatures/imports only), >4KB ->
  archive + skeleton.
- **Safe-mode** - secrets and stack traces = unsafe = 0% compression,
  pass through verbatim (mangling them manufactures hallucinations).
- **Stable prefix (USE-0)** - system instructions/tool schemas stay
  byte-identical at the top; variable content at the end. Never rewrite the
  prefix (breaks prefix caching).

## Output side (O-1..O-5)

| Rule | What it does |
|---|---|
| O-1 | Data-only when machine-consumed; validate JSON before emit |
| O-2 | Length budget picked BEFORE writing (verdict 1 line ... code 150) |
| O-3 | Reasoning scaled to complexity; never narrate dead ends |
| O-4 | Answer-once session cache with staleness guard |
| O-5 | End at the deliverable; no trailing filler |

## Continuity (USE-9) & hygiene

- Durable checkpoint (`RESUME.md`) at the END of any turn with open work;
  read it FIRST next turn. Never re-derive from scratch. ('Before
  compaction' is unobservable and never fired.)
- Hygiene: close unused tabs, files <300 lines, fresh thread every 8-10
  turns.
- Loop detection: same failed action repeating -> STOP, root-cause first.

## USE-7 / USE-8

- **USE-7 tool-surface minimization** - audit always-on MCP schemas with
  toolaudit (est. tokens/call per connector, ranked); disconnect is a USER
  action, never automatic.
- **USE-8 markdown-first** - normalize raw HTML to clean Markdown (mdnorm)
  for web/RAG ingestion.

See also: [[CLI-Reference]], [[Design-Principles]].