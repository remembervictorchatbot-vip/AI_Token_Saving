# Skills

Four skills live in `skills/`. **token-savings is the single source of
token-saving truth**; the others delegate to it with zero duplicated rules.

## token-savings (the unified skill)

One discipline applied to every message: input context assembly + output
generation + code review + continuity. Ships the `toks` + `crl` toolkits
with a 132-test self-test suite. Parts A-F cover behavioral control, context
compression, integration pillars (dedup / continuity / safe-mode / protected
zones), hygiene, provider-agnostic extensions (USE-0/7/8/9), and output
economics (O-1..O-5). See [[Architecture]] and [[CLI-Reference]].

## engineering-discipline (mandatory SOP)

Owns the PHASE model, the PHASE GATE, and LESSONS.md - nothing else. Work
decomposes into phases; a phase may not advance until it passes the gate
(TEST > VERIFY > AUDIT > DEBUG > FIX > ENHANCE > CONFIRM), each step with
evidence ('not run' is NOT 'pass'). Compaction-proof via auto-checkpoint +
auto-resume. Default mode is AUTO-ADVANCE; stops only for a user decision,
an external blocker, or an explicitly accepted gate failure.

## rag-engineering (retrieval playbook)

Synthesized from ragflow / lightrag / RAG-Anything / RAG_Techniques / graphify
/ RagaAI-Catalyst: chunk by semantic+structural boundaries (never fixed token
counts), hybrid search as baseline, graph augmentation for multi-hop, always
rerank top-k, compress retrieved context with token-savings tools, safe-mode
on retrieved chunks, and measure recall@k / faithfulness / task success with
citation traceability.

## token-efficient-code-review (consolidated pointer)

Kept ONLY as a pointer: its `crl` engine was folded into token-savings at
`$TOKS_SKILL_DIR/scripts/crl/`. Use the token-savings code-review path.

## Delegation model

```
engineering-discipline (lifecycle + gate + LESSONS.md)
rag-engineering (retrieval patterns)       -> call into token-savings
token-efficient-code-review (pointer only) -> use token-savings crl path
                                  |
                                  v
              token-savings (THE one place token rules live)
```