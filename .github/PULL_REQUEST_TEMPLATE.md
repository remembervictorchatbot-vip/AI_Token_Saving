---
name: Pull request
about: Submit changes to the toolkit, skills, or docs
title: ''
labels: ''
assignees: ''
---

## Summary
One sentence describing the change.

## Type of change
[ ] Bug fix (backward-compatible)
[ ] New feature (backward-compatible)
[ ] Breaking change
[ ] Documentation only
[ ] CI / tooling

## Related issue
Fixes #____

## Testing
- [ ] `toks selftest` passes (276 tests)
- [ ] `toks demo` passes
- [ ] `python bench/run_bench.py` succeeds
- [ ] CI green (if applicable)

## Checklist
- [ ] No third-party runtime dependencies added
- [ ] No network calls at runtime
- [ ] Claims are labeled **measured** or **claimed** appropriately
- [ ] If `skills/token-savings/scripts/` was touched, I re-synced the Hermes bundle:
  ```bash
  rsync -a --exclude='__pycache__' --exclude='.cache' \
    skills/token-savings/scripts/ dist/hermes/token-savings/scripts/
  ```
- [ ] If the dist/system-prompt bundle changed, I updated the condensed prompt too