---
name: rag-engineering
description: Reusable RAG engineering playbook — how to build retrieval-augmented systems that actually work, distilled from infiniflow/ragflow, hkuds/lightrag, HKUDS/RAG-Anything, NirDiamant/RAG_Techniques, Graphify-Labs/graphify, raga-ai-hub/RagaAI-Catalyst. Use when designing, auditing, or fixing any RAG/retrieval pipeline: chunking, indexing, hybrid search, reranking, graph augmentation, evaluation, observability. Pairs with engineering-discipline (lifecycle) and token-savings (compression + the folded crl codebase-retrieval engine).
agent_created: true
---

# RAG Engineering — Reusable Playbook

Synthesized from the reference repos. Principles first, repo specifics as evidence.

## 1. Chunking (ragflow's "deep doc understanding" lesson)
- Chunk by **semantic + structural boundaries**, not fixed token counts. Tables,
  headings, and code fences must not be split mid-structure.
- Preserve **layout/order metadata** (page, section, position) — free reranking signal.
- For code: chunk by `ast`/function boundaries (the folded `crl` engine in
  `token-savings/scripts/crl/` does closure retrieval) so retrieval returns whole units.

## 2. Indexing & retrieval (lightrag / RAG-Anything)
- **Hybrid search** is the baseline: dense (embeddings) + sparse (BM25/keyword).
  Dense alone misses exact IDs/code; sparse alone misses paraphrase.
- **Graph augmentation** (LightRAG): entity/relation graph for multi-hop queries.
- **Multimodal** (RAG-Anything): keep modality-specific parsers; don't flatten
  images/PDFs into dumb text and lose tables/diagrams.

## 3. Reranking & compression (RAG_Techniques + token-savings)
- Always **rerank** top-k with a cross-encoder before feeding context.
- Apply **context compression** (`token-savings` `toks/astrip.py`, `compress_json`):
  drop boilerplate, keep evidence sentences. Never drop the cited source pointer.
- Limit context to the fewest passages that answer — more isn't better, it dilutes.
- **Safe-mode**: run `toks/safemode.py` on retrieved chunks; secrets/stack traces
  pass through verbatim so the answer never hallucinates from a truncated source.

## 4. Evaluation & observability (RagaAI-Catalyst / graphify)
- Measure: retrieval recall@k, answer faithfulness (no hallucinated citations),
  end-to-end task success. A RAG you can't measure is a RAG you can't trust.
- **Trace** every answer back to its retrieved chunk (citation). No citation = no ship.
- Run **regression tests** on a fixed query set when you change chunking/embedding.

## 5. Anti-patterns
- Naive fixed-size chunking that splits tables/code.
- Dense-only retrieval dropping exact-match IDs.
- Stuffing 20 passages into context "just in case."
- Shipping without a citation traceability check.
- No evaluation harness — tuning blind.
- Compressing retrieved secrets/stack traces (safe-mode violation).

## Integration
- Lifecycle: **engineering-discipline**. Efficiency + dedup + safe-mode + the folded `crl`
  codebase-retrieval engine: **token-savings** (the single source of token-saving truth —
  this skill does NOT duplicate those rules, it references them).
- Note: this playbook is a synthesis of established patterns + the named repos'
  published architectures; validate repo-specific claims against the latest docs
  before production use.
