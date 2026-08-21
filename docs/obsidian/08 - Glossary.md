---
tags: [reference]
---

# 08 - Glossary

| Term | Meaning |
|---|---|
| toks | The general token-saving toolkit CLI (18 subcommands) |
| crl | Code-Review engine (diff-aware retrieval) folded into token-savings |
| DedupCache | In-process cache: first sight keeps full content, repeats return a short ref (JIT-expandable) |
| JIT expansion | Compress aggressively, expand on demand from the cache - compressed is a summary, never a black hole |
| safemode | Classifies text unsafe / caution / safe; unsafe (secrets, stack traces) = 0% compression, verbatim |
| KEEP zones | Protected zones around user literals; survive every compression (marker syntax below) |
| quality_gate | Verifies protected content survived a compression; reverts on a miss |
| RESUME.md | Durable checkpoint: active task, decisions, modified files, open questions, next steps, lessons |
| USE-0 | Stable-prefix rule: stable content on top, never rewritten; variable content at the end |
| USE-7 | Tool-surface minimization: audit always-on MCP/tool schemas, recommend disconnects (never auto) |
| USE-8 | Markdown-first: normalize HTML to clean Markdown for web/RAG ingestion (mdnorm) |
| USE-9 | Session phase-splitting + durable RESUME.md continuity |
| O-1 | Data-only structured output when machine-consumed; validate JSON before emit |
| O-2 | Output length budget picked before writing (verdict 1 line ... code 150 lines) |
| O-3 | Reasoning scaled to complexity; never narrate dead ends |
| O-4 | Answer-once session cache with staleness guard |
| O-5 | End at the deliverable; no trailing filler |
| trim_bash | ANSI strip + collapse repeats + head/tail for shell output |
| summarize_grep | Top hits + count instead of full grep dump |
| compress_json | Drop nulls/debug fields, compact JSON |
| astrip | AST extraction: signatures/imports only, bodies recoverable |
| mdnorm | HTML -> clean Markdown normalization |
| toolaudit | Estimates tokens/call per MCP connector, ranks, flags prune candidates |
| entropy | Diagnostic signal for boilerplate; never an auto-delete |
| compaction | Context compression the host applies when a thread gets long |
| WorkBuddy / Hermes | Harnesses with native skill installs |
| bench | Deterministic stdlib benchmark (run_bench.py, BASELINE.json) |
| cost-estimate | G1 input preflight: estimate token spend before a task (steps x ctx, peak/idle) |
| dedup --diff | Delta re-read: ref on exact repeat, changed-line hunks on edit (measured 77.4%) |
| surface | Read-me-first extractor: one line per symbol/heading/key with line numbers |
| check-syntax | O-6 gate: VALID / INVALID before emitting (py/json/md) |
| audit-session | Self-audit: flags re-reads, prose bloat, loops, unvalidated JSON |
| input-gate | I-1 automatic input processor: dedup -> tiered compress -> safe-mode -> protected zones -> fidelity marker (71.5%) |
| input-meter | Session input cost estimator + recoverable repeat waste |
| I-1..I-4 | Input economics: compress-before-inject, context budget, stable prefix, verify fidelity |
| I-5..I-8 | Autopilot: output-gate before emit, session autopilot loop, environment doctor, auto-checkpoint |
| output-gate | I-5 self-check on a reply before sending: O-2 budget, JSON/fence validity, O-5 filler |
| autopilot | I-6 one-command loop: input-meter + audit-session + output-gate -> NEXT-TURN DIRECTIVES |
| doctor | I-7 environment self-check: is the autopilot wiring actually on? |

Protected-zone marker syntax (write inside code fences to avoid wikilink parsing):

```
[[KEEP]]...[[/KEEP]]
```