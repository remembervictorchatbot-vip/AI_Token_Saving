# Contributing

Thanks for considering a contribution. This project is small, focused, and
quality-gated — please read this before opening a PR.

## Ground rules

- **stdlib only.** The toolkit (`toks/`, `crl/`) must stay pure Python 3.9+
  stdlib. No third-party runtime dependencies, no network calls at runtime.
- **Provider-agnostic.** No provider-specific pricing, model names, or API
  features in skill rules. The principles must hold on any model/harness.
- **True & working only.** Claims get labeled: measured (with evidence) vs
  claimed (not benchmarked here). Don't add a rule because a blog says so —
  add it because it works at the agent layer and you can test it.
- **Quality over savings.** Nothing that drops a fact the user needs.

## Before you open a PR

1. Add or update tests in `skills/token-savings/scripts/tests/`.
2. Run the gate — it must stay green:
   ```bash
   cd skills/token-savings/scripts
   python -m toks.cli selftest   # 179 tests, must pass
   python -m toks.cli demo
   ```
3. If you touch `skills/token-savings`, re-sync the generated Hermes bundle:
   ```bash
   rsync -a --exclude='__pycache__' --exclude='.cache' \
     skills/token-savings/scripts/ dist/hermes/token-savings/scripts/
   ```
   and note it in the PR (the bundle must stay in sync with the source).

## Commit style

Keep commits small and single-purpose. Reference the change it makes, not the
process ("v7: …" is fine; "push pending scope grant" is not).

## Scope of contributions

Ideas welcome for new compression surfaces, edge cases in existing ones, and
adapter improvements for other harnesses. Out of scope: model routing, API
parameter tuning (max_tokens/stop), speculative decoding — those live at the
API/serving layer, outside what this skill can control.
