# FAQ

**Does it really save tokens?**
Yes, measurably at the tool level - 52.1% aggregate on representative
samples ([[Benchmark]]). Agent-level savings scale with how well the model
follows the rules. Reproduce with `python bench/run_bench.py`.

**Will it work with my model / harness?**
The rules are model-agnostic; the toolkit is pure stdlib Python 3.9+ - it
runs anywhere Python runs. Native skills for WorkBuddy and Hermes; a
condensed system-prompt bundle for everything else ([[Installation]]).

**Does it send my data anywhere?**
No. Zero telemetry, zero network calls, zero third-party dependencies.
Everything runs locally and in-process.

**Why not LLMLingua / Outlines / vLLM?**
Powerful but heavyweight (torch, native serving stacks) and they live at the
API/serving layer this project deliberately doesn't control. This toolkit
achieves the same discipline with a pure-stdlib, portable, testable core.

**The dedup claim says 70%+ - is that measured?**
No - it is explicitly labeled 'claimed, not independently benchmarked in
our env'. The measured dedup number (98.3% on a config re-read) comes from
the deterministic bench. Claimed vs measured is always stated.

**How do I know the install works?**
`toks selftest` runs 179 tests and must stay GREEN (CI enforces this on
Python 3.9-3.13). Hermes: `hermes skills list` after install.

**What about the context filter?**
It's lossy by design (one-way) - bulk tool output is compressed before the
model sees it; keep your own logs for exact data. Protected zones and
secrets always pass verbatim. Cross-request dedup is intentionally off.

See also: [[Home]], [[DeepSeek-Harness-Adapter]].