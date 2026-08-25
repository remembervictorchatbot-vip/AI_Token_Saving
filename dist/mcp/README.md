# toks-mcp — MCP adapter (v15)

Exposes the toks toolkit as a **Model Context Protocol stdio server** so any
MCP host (Claude Desktop, Hermes, Codex-style harnesses) can use token-saving
without shell access.

## Design: lazy-loading meta-tool pattern

Only 5 tool schemas are advertised (~127 tok total — measured). No SDK
dependency; pure stdlib JSON-RPC over stdio, protocol `2024-11-05`
(echoes the client's version).

| Tool | Wraps | Purpose |
|---|---|---|
| `compress_context` | gate.gate_content | tiered compression + [[KEEP]] + safemode |
| `retrieve_original` | ccr.CCR.retrieve | verbatim original by `[ccr:<hash>]` marker |
| `search_tools` | toolsearch | BM25 search + one-line index over a manifest |
| `skills_search` | skills_mgmt.search_index | find installed skills without loading bodies |
| `auto_sweep` | full_auto.auto | one-call health report + directives |

## Install

**Claude Desktop** (`claude_desktop_config.json`):
```json
{"mcpServers": {"toks": {
  "command": "python3",
  "args": ["/path/to/AI_Token_Saving/dist/mcp/toks_mcp_server.py"]}}}
```

**Hermes** (`~/.hermes/config.yaml`, under `mcp_servers:`):
```yaml
  toks:
    command: python3
    args:
      - /path/to/AI_Token_Saving/dist/mcp/toks_mcp_server.py
      - --scripts-dir
      - /path/to/AI_Token_Saving/skills/token-savings/scripts
    timeout: 60
    connect_timeout: 30
    enabled: true
```

Verify from the repo root: `toks discover --live` → toks appears with
`LIVE 5 tools`.

## Codex / OpenCode / OpenWork

These hosts consume skills + CLI rather than MCP. The MCP server still works
alongside them — register it in the host's `mcp.json` with the same shape as
Claude Desktop above. The skill copy in `.opencode/skills/` stays the
primary instruction layer there.

## WorkBuddy

`cp -R skills/* ~/.workbuddy/skills/` installs everything; `bin/toks`
resolves its own dir via `$TOKS_SKILL_DIR` → `$HERMES_SKILL_DIR` → autodetect.
The MCP server is optional (WorkBuddy has shell access and calls `toks`
directly).

## Test

```bash
python3 dist/mcp/test_server.py     # 7 integration tests over real stdio
```

## Safety

- Recommend-only: nothing is archived/disconnected by this server.
- Safemode runs inside compress_context — secrets pass verbatim.
- CCR cache bounded (LRU 200 / 50 MB / 30-day TTL).
- Stdout carries only JSON-RPC; diagnostics go to stderr.
