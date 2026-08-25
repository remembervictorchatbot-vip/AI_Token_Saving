---
tags: [adapters deepseek hermes workbuddy]
---

# 06 - Adapters

How the discipline ships to different harnesses.

## Universal path (any harness with a system prompt + model endpoint)

1. Paste [dist/system-prompt/token-savings-prompt.md](../../dist/system-prompt/token-savings-prompt.md)
   at the TOP of the system prompt (18 standing rules: input discipline,
   output discipline, continuity & hygiene).
2. Optional context filter: run [dist/deepseek-harness/toks_filter.py](../../dist/deepseek-harness/toks_filter.py)
   as an OpenAI-compatible proxy that compresses request bodies before the
   model sees them; point the harness's base_url at http://127.0.0.1:8090/v1.
3. Optional portable CLI: add skills/token-savings/bin to PATH.

## DeepSeek-harness filter

OpenAI-compatible /v1/chat/completions proxy, pure stdlib, zero changes to
the harness. Env vars:

| Var | Default | Meaning |
|---|---|---|
| TOKS_UPSTREAM | (required) | real model endpoint, e.g. https://api.deepseek.com/v1 |
| TOKS_PORT | 8090 | listen port |
| TOKS_MIN_COMPRESS | 800 | minimum body size before compressing |
| TOKS_SKILL_DIR | autodetect | skill dir resolution |
| TOKS_QUIET | off | quiet logging |

Properties: repeats collapse within a single request (cross-request dedup
intentionally NOT used - no JIT expansion at the proxy); protected zones and
secrets always pass verbatim; lossy by design (one-way) - keep your own logs
for exact data. Verify with test_filter.py + GET /health.

## Hermes Agent

Native skill at [dist/hermes/token-savings/](../../dist/hermes/token-savings/):
install with 'cp -R dist/hermes/token-savings ~/.hermes/skills/' then
'hermes skills list'. The bundle is GENERATED from skills/ by
[build_hermes_bundle.py](../../build_hermes_bundle.py) - it syncs scripts/
and bin/, and PRESERVES the hand-maintained Hermes SKILL.md. CI enforces
sync via 'python build_hermes_bundle.py --check'.

## WorkBuddy

'cp -R skills/* ~/.workbuddy/skills/' - native, 276/276 tests, gated releases.

## Others (Claude Code / Codex / OpenCode-style)

Copy skills/token-savings, ensure Python 3.9+ on PATH (behavioral rules
port). CLI agents can point their OpenAI-compatible config at the filter
(e.g. OPENAI_BASE_URL=http://127.0.0.1:8090/v1) and add the prompt bundle to
the model's system prompt.

See also: [[03 - CLI Reference]] (toolkit), [[11 - Development]] (bundle build).