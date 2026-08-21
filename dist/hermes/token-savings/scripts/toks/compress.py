"""Lossless-ish compression primitives (sqz JSON pipeline + token-optimizer surfaces).

Principles:
- JSON: drop nulls + debug fields, compact dump. Values we keep are unchanged.
- Bash output: strip ANSI, collapse repeated lines, head/tail truncate.
- Grep: top hits + total count, not the full dump.
- Skeleton: signatures/imports only (lossy BY DESIGN) - full code stays recoverable.
"""
import json
import re

DEBUG_KEYS = {
    "debug", "trace", "stack", "stacktrace", "raw",
    "_internal", "meta_debug", "verbose", "log",
}
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def compress_json(obj, drop_debug: bool = True) -> str:
    """Drop nulls + debug fields, compact serialize. Keeps all real values."""
    return json.dumps(_clean(obj, drop_debug), ensure_ascii=False, separators=(",", ":"))


def _clean(obj, drop_debug):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if v is None:
                continue
            if drop_debug and isinstance(k, str) and k.lower() in DEBUG_KEYS:
                continue
            out[k] = _clean(v, drop_debug)
        return out
    if isinstance(obj, list):
        return [_clean(v, drop_debug) for v in obj]
    return obj


def trim_bash(output: str, max_lines: int = 40, collapse_repeats: int = 3) -> str:
    lines = strip_ansi(output).splitlines()
    collapsed, run = [], []
    for ln in lines:
        if run and ln == run[-1]:
            run.append(ln)
        else:
            if len(run) > collapse_repeats:
                collapsed.append(f"[... x{len(run)} identical lines collapsed ...]")
            elif run:
                collapsed.extend(run)
            run = [ln]
    if len(run) > collapse_repeats:
        collapsed.append(f"[... x{len(run)} identical lines collapsed ...]")
    elif run:
        collapsed.extend(run)
    if len(collapsed) > max_lines:
        head = max_lines // 2
        tail = max_lines - head
        collapsed = (
            collapsed[:head]
            + [f"[... {len(collapsed) - max_lines} lines omitted ...]"]
            + collapsed[-tail:]
        )
    return "\n".join(collapsed)


def summarize_grep(results: str, top: int = 10) -> str:
    lines = [line for line in results.splitlines() if line.strip()]
    total = len(lines)
    if total <= top:
        return results
    return "\n".join(lines[:top]) + f"\n[+{total - top} more matches; request expand for full]"


def skeleton(code: str, lang: str = "py") -> str:
    """Structure-only view: signatures/imports/comments, bodies dropped."""
    out = []
    for ln in code.splitlines():
        s = ln.strip()
        if lang == "py":
            if re.match(r"^(def |class |import |from |@|#)", s):
                out.append(ln)
        else:
            if re.match(r"^\s*(public|private|protected|func|function|def|class|import|package|use|#|//|/\*)", s):
                out.append(ln)
    return "\n".join(out) + "\n[ skeleton: bodies omitted; full available via expand ]"
