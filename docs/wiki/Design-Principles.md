# Design Principles

Synthesized from three open-source approaches - logic kept, heavy
dependencies rejected:

| Source | Kept (portable logic) | Rejected |
|---|---|---|
| ojuschugh1/sqz | content-hash dedup, lossless pipeline, entropy safe-mode | Rust binary |
| alexgreensh/token-optimizer | multi-surface compression, checkpoint, quality gate, loop detection | hook daemon, SQLite dashboard |
| vaibkumr/prompt-optimizer | protected zones, entropy as *diagnostic* | blind entropy delete (drops accuracy) |

## Core rules

1. **Quality wins over savings** - if a compression would drop meaning, do
   not compress.
2. **Protected zones survive everything** - user literals in protected
   zones; quality-gate verifies on every pass, reverts on a miss.
3. **Entropy is diagnostic, not a delete button** - find boilerplate to
   trim, never auto-delete (blind entropy drops accuracy 0.32->0.22 in
   prompt-optimizer's own eval).
4. **Stable prefix never rewritten (USE-0)** - dedup only the variable
   suffix; rewriting the prefix breaks prefix caching everywhere.
5. **Honest labeling** - 'claimed' vs 'measured' is stated explicitly
   (dedup 70%+ = claimed; bench numbers = measured).
6. **Safe-mode boundaries** - secrets/stack traces pass verbatim;
   truncating them manufactures hallucinations.
7. **Continuity is a file, not an event** - RESUME.md written at end of
   turn (observable), never 'before compaction' (unobservable).

## Out of scope (deliberately)

- Re-implementing sqz's Rust binary or token-optimizer's hook daemon.
- API-layer knobs (max_tokens, stop sequences, model routing) - behavioral
  rules only.
- LLMLingua / Outlines / vLLM - powerful but heavyweight (torch, native
  serving) and live at the API/serving layer this project doesn't control.

See also: [[Architecture]], [[Benchmark]].