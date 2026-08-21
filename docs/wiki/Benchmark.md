# Benchmark

Deterministic, stdlib-only, provider-agnostic measurement of the TOOLS on
representative samples. NOT an end-to-end agent session.

| Surface | Sample | Before | After | Saved |
|---|---|---|---|---|
| dedup (file-hash) | config re-read (2nd read) | 1,059 | 18 | **98.3%** |
| dedup --diff (v8) | config re-read after edit | 1,067 | 241 | **77.4%** |
| summarize_grep | 150 grep hits | 4,449 | 334 | **92.5%** |
| astrip | ~150-line Python module | 6,816 | 1,420 | **79.2%** |
| trim_bash | build log w/ ANSI + repeats | 3,519 | 877 | **75.1%** |
| O-1 data-only | chat reply -> table | 345 | 98 | **71.6%** |
| compress_json | 500-item API payload (nulls+debug) | 37,293 | 21,243 | **43.0%** |
| mdnorm | 120-paragraph docs page | 14,118 | 10,109 | **28.4%** |
| **Aggregate** | | **68,666** | **34,340** | **50.0%** |

## Reproduce

```bash
python bench/run_bench.py          # full run
python bench/run_bench.py --check  # regression gate (CI uses this)
```

Baseline: `bench/BASELINE.json`; task samples: `bench/tasks.py`.

## Honest scope

- Tool-level numbers only. End-to-end session savings also depend on model
  compliance (frontier models comply better than small local ones).
- No inflated claims - everything is reproducible.
- Dedup '70%+ over long sessions' is labeled **claimed, not benchmarked**.
- crl function-mode: 85.2% / 47.3% input saved on leaf changes (measured).

See also: [[Architecture]], [[FAQ]].