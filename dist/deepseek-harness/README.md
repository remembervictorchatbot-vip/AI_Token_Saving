# DeepSeek-harness adapter 🌍

Two pieces, both portable and pure-stdlib:

| Piece | What it does |
|---|---|
| `toks_filter.py` | OpenAI-compatible **context filter** — sits between your harness and the model, compresses request bodies (repeat blobs, big JSON, HTML, logs) before they reach the model. Zero changes to the harness. |
| `../system-prompt/token-savings-prompt.md` | Condensed standing-rules bundle — inject at the TOP of your harness's system prompt (fluff-strip, length budgets, dedup discipline, continuity). Canonical copy lives in `dist/system-prompt/`; copy it alongside this folder for a self-contained distribution. |

## Assumptions (stated honestly)

Built for the common DeepSeek-harness shape: an **OpenAI-compatible
`/v1/chat/completions` endpoint** with Python 3.9+ available on the host. If your
harness is something else (a native skill loader, a plugin system), tell me the
mechanism and I'll add that adapter — the behavioral prompt bundle works
regardless.

## Wiring (3 shapes)

**1. DeepSeek API (cloud)** — run the filter, point the harness at it:
```bash
TOKS_UPSTREAM=https://api.deepseek.com/v1 python3 toks_filter.py   # :8090
# then set your harness's base_url to http://127.0.0.1:8090/v1
```

**2. Local server (LM Studio / llama.cpp / vLLM)** — same filter, different upstream:
```bash
TOKS_UPSTREAM=http://localhost:1234/v1 python3 toks_filter.py
# harness base_url -> http://127.0.0.1:8090/v1
```

**3. CLI agents (Qwen Code / OpenCode)** — point their OpenAI-compatible config at
the filter (e.g. `OPENAI_BASE_URL=http://127.0.0.1:8090/v1`) and add the prompt
bundle to the model's system prompt.

## Verify

```bash
python3 test_filter.py   # json compressed · repeat→§ref · [[KEEP]] intact · passthrough
curl http://127.0.0.1:8090/health   # {"status":"ok"}
```

## Honest limits

- **Lossy by design (one-way).** Bulk tool output is compressed before the model
  sees it; the exact original isn't recoverable from model context. Keep your own
  logs for exact data.
- `[[KEEP]]…[[/KEEP]]` zones and secrets (safemode) always pass through verbatim.
- Cross-request dedup is intentionally NOT used (no JIT expansion at the proxy);
  repeats collapse only within a single request, where the full copy is present.
- Env: `TOKS_UPSTREAM` (required), `TOKS_PORT` (8090), `TOKS_MIN_COMPRESS` (800),
  `TOKS_SKILL_DIR`, `TOKS_QUIET`.
