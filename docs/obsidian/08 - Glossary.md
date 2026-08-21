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
| [[KEEP]] zones | Protected zones around user literals; survive every compression |
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