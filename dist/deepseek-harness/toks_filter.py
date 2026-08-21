#!/usr/bin/env python3
"""toks filter — OpenAI-compatible context compressor (DeepSeek-harness adapter).

Sits between any OpenAI-compatible harness and the model endpoint. Compresses
request bodies (repeat blobs, big JSON, HTML, logs) BEFORE they reach the model,
then forwards to the real upstream and returns the response verbatim.

Why this shape: most DeepSeek harnesses (custom Python loops, Qwen Code, OpenCode,
LM Studio / llama.cpp servers) speak OpenAI's /v1/chat/completions. Point their
base_url at this server — zero changes to the harness.

Env:
  TOKS_UPSTREAM   real endpoint, e.g. https://api.deepseek.com/v1
                  or http://localhost:1234/v1 (LM Studio / llama.cpp)
  TOKS_PORT       listen port (default 8090)
  TOKS_SKILL_DIR  skill dir override (default: repo-relative auto-detect)

Run:    python3 toks_filter.py
Test:   python3 test_filter.py

Lossy-by-design (one-way proxy): bulk tool output is compressed and the exact
original is NOT recoverable from the model's context — keep your own logs for
exact data. [[KEEP]] zones and secrets always pass through verbatim (v9: the
request body runs the automatic input gate - tiered compression with protected
zones kept verbatim and a never-grow guarantee).
"""
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("TOKS_PORT", "8090"))
UPSTREAM = os.environ.get("TOKS_UPSTREAM", "").rstrip("/")
MIN_COMPRESS = int(os.environ.get("TOKS_MIN_COMPRESS", "800"))  # chars


def _scripts_dir():
    d = os.environ.get("TOKS_SKILL_DIR")
    if d and os.path.isdir(os.path.join(d, "scripts", "toks")):
        return os.path.join(d, "scripts")
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(here, "..", "..", "skills", "token-savings", "scripts")
    return cand if os.path.isdir(os.path.join(cand, "toks")) else None


_SCRIPTS = _scripts_dir()
if _SCRIPTS:
    sys.path.insert(0, _SCRIPTS)
    from toks import compress, mdnorm, safemode, gate  # noqa: E402
else:
    print("WARN: toks toolkit not found (set TOKS_SKILL_DIR). Running passthrough.",
          file=sys.stderr)
    compress = mdnorm = safemode = gate = None

KEEP_OPEN, KEEP_CLOSE = "[[KEEP]]", "[[/KEEP]]"


def compress_content(text: str, seen: dict) -> str:
    """Compress one message's text content. Safe: never touches KEEP zones or
    secrets; repeated identical blobs collapse to a same-request reference."""
    if not text or len(text) < MIN_COMPRESS:
        return text
    if KEEP_OPEN in text or KEEP_CLOSE in text:
        return text
    if safemode and safemode.risk_level(text) == "unsafe":
        return text
    # exact duplicate within this request -> reference the earlier full copy
    key = hash(text)
    if key in seen:
        return f"§ref:{key & 0xffffffff:08x}§ (identical content earlier in this conversation)"
    seen[key] = True

    # v9: run the automatic input gate (safemode -> tiered compression ->
    # protected-zone protection). No marker in proxy mode: idempotency and
    # cross-request dedup stay intentionally off here (no JIT expansion at
    # the proxy - see README).
    if gate:
        return gate.gate_content(text, use_dedup=False,
                                 min_compress=MIN_COMPRESS, mark=False)

    stripped = text.strip()
    # JSON payloads -> compress_json
    if stripped[:1] in "[{" and compress:
        try:
            return compress.compress_json(json.loads(text))
        except Exception:
            pass
    # HTML -> clean markdown
    if mdnorm and ("<html" in text[:500].lower() or "<!doctype" in text[:500].lower()):
        return mdnorm.html_to_markdown(text)
    # everything else long -> collapse repeats + head/tail (generous)
    if compress:
        return compress.trim_bash(text, max_lines=200, collapse_repeats=3)
    return text


def filter_messages(messages):
    seen = {}
    out = []
    for m in messages:
        if not isinstance(m, dict):
            out.append(m)
            continue
        content = m.get("content")
        if isinstance(content, str):
            m = dict(m)
            m["content"] = compress_content(content, seen)
        out.append(m)
    return out


class Handler(BaseHTTPRequestHandler):
    def _forward(self, body=None):
        url = UPSTREAM + self.path
        req = urllib.request.Request(url, data=body, method=self.command,
                                     headers={k: v for k, v in self.headers.items()
                                              if k.lower() not in ("host", "content-length")})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                if k.lower() not in ("content-length", "transfer-encoding", "connection"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        if "/completions" in self.path and UPSTREAM and raw:
            try:
                body = json.loads(raw)
                if isinstance(body, dict) and isinstance(body.get("messages"), list):
                    body["messages"] = filter_messages(body["messages"])
                    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
            except Exception:
                pass  # malformed -> forward verbatim
        self._forward(raw)

    def do_GET(self):
        if self.path == "/health":
            data = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._forward()

    def log_message(self, *args):
        if os.environ.get("TOKS_QUIET"):
            return
        super().log_message(*args)


def main():
    if not UPSTREAM:
        sys.exit("TOKS_UPSTREAM is required (e.g. https://api.deepseek.com/v1)")
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"toks filter on :{PORT} -> {UPSTREAM} (min compress {MIN_COMPRESS} chars)")
    print("toolkit:", _SCRIPTS or "MISSING - passthrough mode")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
