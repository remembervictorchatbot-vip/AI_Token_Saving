# Installation

## Universal path (any harness with a system prompt + model endpoint)

Works everywhere - WorkBuddy, Claude Code, Codex, OpenCode, Qwen Code,
custom DeepSeek harnesses, AI Studio, local agents...

```bash
# 1. Behavioral rules - paste dist/system-prompt/token-savings-prompt.md
#    at the TOP of your system prompt.

# 2. Context filter - compress requests before they reach the model:
TOKS_UPSTREAM=https://api.deepseek.com/v1 python3 dist/deepseek-harness/toks_filter.py
#    then point your harness base_url at http://127.0.0.1:8090/v1
#    (LM Studio / llama.cpp: TOKS_UPSTREAM=http://localhost:1234/v1)

# 3. Optional portable CLI on PATH:
export PATH="$PWD/skills/token-savings/bin:$PATH"
toks selftest        # 132 tests, all must pass
```

## Native installs

| Platform | Install |
|---|---|
| **WorkBuddy** | `cp -R skills/* ~/.workbuddy/skills/` |
| **Hermes Agent** | `cp -R dist/hermes/token-savings ~/.hermes/skills/` then `hermes skills list` |
| **Claude Code / Codex / OpenCode-style** | copy `skills/token-savings`, ensure Python 3.9+ on PATH |
| **Anything else** | universal path above - it always works |

## Target matrix

| Target | Status |
|---|---|
| Any harness w/ model endpoint | universal path - always works |
| DeepSeek-style harness | dedicated adapter (filter + prompt bundle) |
| WorkBuddy | native - 132/132 tests - gated releases |
| Hermes Agent | verified (installs, registers, enabled) |
| Codex / Claude Code / OpenCode-style | behavioral rules port; needs skill conversion |
| Ollama / LM Studio (model servers) | no agent loop - condensed prompt applies |

The toolkit is location-independent: `bin/toks` resolves its skill dir via
`$TOKS_SKILL_DIR` -> `$HERMES_SKILL_DIR` -> autodetect. No hardcoded paths.

> `dist/hermes/token-savings/scripts/` is a **generated bundle** (copy of
> `skills/token-savings/scripts/`); the source of truth is `skills/`.

See also: [[DeepSeek-Harness-Adapter]], [[CLI-Reference]].