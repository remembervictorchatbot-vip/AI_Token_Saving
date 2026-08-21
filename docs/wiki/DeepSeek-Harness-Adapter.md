# DeepSeek-Harness Adapter

Two pieces, both portable and pure-stdlib:

| Piece | What it does |
|---|---|
| `toks_filter.py` | OpenAI-compatible **context filter** - sits between the harness and the model, compresses request bodies (repeat blobs, big JSON, HTML, logs) before they reach the model. Zero changes to the harness. |
| `token-savings-prompt.md` | Condensed standing-rules bundle - inject at the TOP of the system prompt. Canonical copy: `dist/system-prompt/`. |

## Wiring (3 shapes)

**1. DeepSeek API (cloud)**
```bash
TOKS_UPSTREAM=https://api.deepseek.com/v1 python3 toks_filter.py   # :8090
# set your harness base_url to http://127.0.0.1:8090/v1
```

**2. Local server (LM Studio / llama.cpp / vLLM)**
```bash
TOKS_UPSTREAM=http://localhost:1234/v1 python3 toks_filter.py
# harness base_url -> http://127.0.0.1:8090/v1
```

**3. CLI agents (Qwen Code / OpenCode)** - point their OpenAI-compatible
config at the filter (e.g. `OPENAI_BASE_URL=http://127.0.0.1:8090/v1`) and
add the prompt bundle to the model's system prompt.

## Env vars

| Var | Default | Meaning |
|---|---|---|
| TOKS_UPSTREAM | (required) | real model endpoint |
| TOKS_PORT | 8090 | listen port |
| TOKS_MIN_COMPRESS | 800 | minimum body size before compressing |
| TOKS_SKILL_DIR | autodetect | skill dir resolution |
| TOKS_QUIET | off | quiet logging |

## Verify

```bash
python3 test_filter.py   # json compressed - repeat->ref - protected zones intact - passthrough
curl http://127.0.0.1:8090/health   # {"status":"ok"}
```

## Honest limits

- **Lossy by design (one-way)** - bulk tool output is compressed before the
  model sees it; keep your own logs for exact data.
- Protected zones and secrets always pass through verbatim.
- Cross-request dedup is intentionally NOT used (no JIT expansion at the
  proxy); repeats collapse only within a single request.

See also: [[Installation]], [[CLI-Reference]].