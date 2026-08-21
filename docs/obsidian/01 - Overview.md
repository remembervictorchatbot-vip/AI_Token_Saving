---
tags: [token-savings]
---

# 01 - Overview

**AI Token Saving** ('little lovely planet') is a quality-preserving token &
credit saving discipline for AI agents:

> Context is expensive. Re-pasted files, verbose tool output, and padded
> replies burn tokens and credits on every message. This project cuts that
> waste **without dropping a single fact the user needs**.

## Positioning

- **Model-agnostic** - behavioral rules work on any model.
- **Harness-agnostic** - universal system-prompt bundle + context filter for
  anything with a model endpoint; native skills for WorkBuddy and Hermes.
- **Pure stdlib Python 3.9+** - zero dependencies, zero telemetry, zero
  network calls. Everything runs locally and in-process.

## The four promises

1. **Never re-paste what you already read** - dedup (returns a short ref)
2. **Never send markup when meaning is enough** - compress / normalize
3. **Never generate prose when data will do** - output discipline
4. **Never lose the one fact that mattered** - protected zones

## Quick start (universal, any harness)

1. Paste [[06 - Adapters|the system-prompt bundle]] at the TOP of your system prompt.
2. Optional context filter: run dist/deepseek-harness/toks_filter.py with
   TOKS_UPSTREAM set, point the harness at http://127.0.0.1:8090/v1.
3. Optional portable CLI: add skills/token-savings/bin to PATH, then
   'toks selftest' (132 tests, must pass).

## Measured impact (tool-level, deterministic)

Aggregate **49.6% input savings** on representative samples - see
[[04 - Benchmark]].

## Reading order in this vault

[[02 - Architecture]] > [[03 - CLI Reference]] > [[04 - Benchmark]] >
[[05 - Skills]] > [[06 - Adapters]] > [[08 - Glossary]]