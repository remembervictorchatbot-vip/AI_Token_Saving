# Tool-level token-savings benchmark (v7 P3)

_Deterministic, stdlib-only, provider-agnostic (est tokens = chars/4). Measures the TOOLS on representative samples — NOT an end-to-end agent session. Agent-level savings on each target runtime (WorkBuddy / Hermes / DeepSeek harness) are a separate verification pending that runtime._

| Surface | Sample | Before chars | After chars | Saved % | Est tok before | Est tok after |
|---------|--------|-------------|-------------|---------|----------------|---------------|
| dedup (file-hash) | config re-read (2nd read) | 1059 | 18 | 98.3% | 264 | 4 |
| compress_json | 500-item API payload (nulls+debug) | 37293 | 21243 | 43.0% | 9323 | 5310 |
| astrip | ~150-line Python module | 6816 | 1420 | 79.2% | 1704 | 355 |
| trim_bash | build log w/ ANSI + repeats | 3519 | 877 | 75.1% | 879 | 219 |
| summarize_grep | 150 grep hits | 4449 | 334 | 92.5% | 1112 | 83 |
| mdnorm | 120-paragraph docs page | 14118 | 10109 | 28.4% | 3529 | 2527 |
| O-1 data-only | chat reply -> table | 345 | 98 | 71.6% | 86 | 24 |
| dedup --diff (delta) | config re-read after edit | 1067 | 241 | 77.4% | 266 | 60 |

**Aggregate across samples: 68,666 -> 34,340 chars (50.0% saved).**
