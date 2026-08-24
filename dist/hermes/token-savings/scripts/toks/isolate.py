"""Sub-agent context isolation brief builder (v11).

Multi-agent fan-out wastes the most tokens when children inherit parent
history. The multi-agent-token-optimization pattern: a child gets ZERO
conversation history - only goal + context + paths + constraints, and state
updates flow back as deltas, never full dumps.

`isolate` builds that minimal brief deterministically and flags leaks:
  - past-conversation references ("as we discussed", "earlier", "previous turn")
  - full-state dumps (pasted blobs > 2000 chars in --context)
  - duplicate paths / duplicated context lines

Pure stdlib, deterministic.
"""
import re


HISTORY_LEAK_RE = re.compile(
    r"\b(as we discussed|earlier (in|this) (session|chat|conversation)|"
    r"previous turn|above conversation|as mentioned before|"
    r"see (our|the) earlier)\b", re.I)


def build_brief(goal: str, context: str = "", paths: str = "",
                output_contract: str = "") -> dict:
    path_list, seen = [], set()
    for p in (s.strip() for s in re.split(r"[,\n;]", paths)):
        if p and p not in seen:
            seen.add(p)
            path_list.append(p)
    ctx_lines, seen_l = [], set()
    for ln in context.splitlines():
        key = ln.strip()
        if key and key not in seen_l:
            seen_l.add(key)
            ctx_lines.append(ln)
    clean_ctx = "\n".join(ctx_lines)
    warnings = []
    if HISTORY_LEAK_RE.search(goal + "\n" + clean_ctx):
        warnings.append("history-leak: brief references prior conversation - rewrite self-contained")
    if len(clean_ctx) > 2000:
        warnings.append("state-dump: context {} chars > 2000 - send deltas/pointers instead".format(len(clean_ctx)))
    brief_lines = ["Goal:", goal]
    if clean_ctx:
        brief_lines += ["", "Context:", clean_ctx]
    if path_list:
        brief_lines += ["", "Paths:", *[("  " + p) for p in path_list]]
    if output_contract:
        brief_lines += ["", "Output contract:", output_contract]
    brief = "\n".join(brief_lines)
    est = lambda s: max(1, len(s) // 4)
    return {
        "brief": brief,
        "warnings": warnings,
        "tok_est": est(brief),
        "paths": path_list,
    }


def format_report(res: dict) -> str:
    lines = [
        "isolated child brief ({} tok est)".format(res["tok_est"]),
        "-" * 40,
        res["brief"],
        "-" * 40,
    ]
    lines += ["[WARN] " + w for w in res["warnings"]] or ["no leaks detected"]
    return "\n".join(lines)
