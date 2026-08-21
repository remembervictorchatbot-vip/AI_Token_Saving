---
name: token-efficient-code-review
description: CONSOLIDATED. The token-efficient code-review retrieval engine (`crl`) now lives inside the unified `token-savings` skill at `$TOKS_SKILL_DIR/scripts/crl/`. Use the `token-savings` skill for all token-saving work, including code review (its PART C1/C2 + the `crl` path). This skill is kept only as a pointer to avoid duplicate/overlapping token-saving skills.
agent_created: true
---

# Token-Efficient Code Review — CONSOLIDATED into `token-savings`

This skill's retrieval engine (`crl`) has been folded into the unified
**`token-savings`** skill. Do not maintain two token-saving skills.

## What moved
- `scripts/crl/` (index / chunker / retrieve / analyze / preflight / tokens / cli) →
  `$TOKS_SKILL_DIR/scripts/crl/`
- `scripts/demo.py` → `$TOKS_SKILL_DIR/scripts/crl_demo.py`
- `scripts/sample_repo/` → `$TOKS_SKILL_DIR/scripts/sample_repo/`

## Use instead
Load **`token-savings`** and use its code-review path:

```bash
cd "$TOKS_SKILL_DIR/scripts"
python -m crl.cli index <repo>
python -m crl.cli review <repo> --changed app/utils.py --mode function --show
python -m crl.cli summary <repo> --files module.txt --top 12
```

All original mechanics (diff-aware closure retrieval, deterministic-first
pre-flight, risk-ranked summary, staleness fingerprint, VBA support) are intact and
verified (`python crl_demo.py` → 85% / 47% input saved).
