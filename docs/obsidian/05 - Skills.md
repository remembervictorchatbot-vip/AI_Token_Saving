---
tags: [skills]
---

# 05 - Skills

Four skills live in [skills/](../../skills/). **token-savings is the single
source of token-saving truth**; the others delegate to it and contain ZERO
duplicated token rules.

## 1. token-savings (the unified skill)

One discipline applied to every message: input context assembly + output
generation + code review + continuity. Ships the toks + crl toolkits with a
132-test self-test suite. Parts A-F cover behavioral control, context
compression, integration pillars (dedup / continuity / safe-mode / protected
zones), hygiene, provider-agnostic extensions (USE-0/7/8/9), and output
economics (O-1..O-5).

Full map: [[01 - Overview]] / [[02 - Architecture]] / [[03 - CLI Reference]].

## 2. engineering-discipline (mandatory SOP)

Owns the PHASE model, the PHASE GATE, and LESSONS.md - nothing else. Work
decomposes into phases; a phase may not advance until it passes the gate
(TEST > VERIFY > AUDIT > DEBUG > FIX > ENHANCE > CONFIRM), each step with
evidence ('not run' is NOT 'pass'). Continuity is compaction-proof via
auto-checkpoint + auto-resume. Default mode is AUTO-ADVANCE; it stops only
for a user decision, an external blocker, or a gate failure the user must
accept.

## 3. rag-engineering (retrieval playbook)

Synthesized from ragflow / lightrag / RAG-Anything / RAG_Techniques / graphify
/ RagaAI-Catalyst: chunk by semantic+structural boundaries (never fixed token
counts), hybrid search as baseline, graph augmentation for multi-hop, always
rerank top-k, compress retrieved context with token-savings tools, safe-mode
on retrieved chunks, and measure recall@k / faithfulness / task success with
citation traceability.

## 4. token-efficient-code-review (consolidated pointer)

Kept ONLY as a pointer: its crl engine was folded into token-savings at
$TOKS_SKILL_DIR/scripts/crl/. Use the token-savings code-review path instead.

## Delegation model

```
engineering-discipline (lifecycle + gate + LESSONS.md)
rag-engineering (retrieval patterns)       -> call into token-savings
token-efficient-code-review (pointer only) -> use token-savings crl path
                                  |
                                  v
              token-savings (THE one place token rules live)
```

See also: [[06 - Adapters]] for how skills get installed per harness.