"""Lightweight, token-cheap analysis: summarize without dumping full source.

Goal: decide WHERE a surgical review is worth it, instead of reviewing
everything. Produces a compact markdown report (size map, complexity hotspots,
deterministic pre-flight findings). Token cost is a few hundred tokens vs
tens of thousands for a whole-module dump.

This is the "partial analysis" / "lightweight summary" tier: it answers
"what should I review and where are the risks?" for a fraction of the tokens
of a full review.
"""

import os
import re

from .tokens import estimate
from .preflight import run_preflight

DECISION_RE = re.compile(
    r'^\s*(?:If\b|ElseIf\b|Else\b|Select\s+Case\b|Case\b|For\b|While\b|Do\b|'
    r'With\b|On\s+Error\b)',
    re.I,
)
CALL_RE = re.compile(r'\b([A-Za-z_]\w*)\s*\(')


def complexity(source):
    """Rough McCabe-style proxy: decision/loop keywords + distinct calls."""
    decisions = len(DECISION_RE.findall(source))
    calls = len(set(CALL_RE.findall(source)))
    return decisions + calls  # +1 baseline path implied


def risk_score(row, flagged_names, flagged_lines):
    """Blend size, complexity and deterministic findings into a review priority.

    Pure size ranking is what let a 40-line silent-failure bug outrank nothing at
    all -- small procedures never surface. Complexity per-token and lint hits are
    what actually correlate with defects, so they dominate the score and size is
    only a mild tie-breaker.
    """
    tok = max(row["tok"], 1)
    hit = 0.0
    if row["name"].lower() in flagged_names:
        hit += 30.0
    # any deterministic finding landing inside this procedure's line span
    for ln in flagged_lines:
        if row["start"] <= ln <= row["end"]:
            hit += 30.0
            break
    # ABSOLUTE complexity, not density. Density (cx per token) explodes on
    # 3-line helpers and buries the 500-line financial procedures where the
    # defects actually live. Size is damped via sqrt so it informs the ranking
    # without collapsing it back into a pure size sort.
    return hit + row["cx"] + 0.5 * (tok ** 0.5)


def _parse_flags(preflight):
    """Extract procedure names and line numbers cited by the pre-flight block."""
    names, lines = set(), set()
    for m in re.finditer(r'^PROC\s+([A-Za-z_]\w*)\s*:', preflight, re.M):
        names.add(m.group(1).lower())
    for m in re.finditer(r'^L(\d+):', preflight, re.M):
        lines.add(int(m.group(1)))
    return names, lines


def summarize(idx, files=None, top_n=15):
    """Return a compact markdown report. `files` restricts scope (None = all)."""
    if files:
        modules = []
        for f in files:
            mod = idx.module_of(f)
            if mod in idx.by_module:
                modules.append(mod)
    else:
        modules = list(idx.by_module.keys())

    rows = []
    total_tok = 0
    scope_files = set()
    for mod in modules:
        for c in idx.by_module.get(mod, []):
            tok = estimate(c.source)
            total_tok += tok
            scope_files.add(c.file)
            rows.append({
                "module": mod, "name": c.name, "kind": c.kind,
                "start": c.start_line, "end": c.end_line,
                "tok": tok, "cx": complexity(c.source),
            })
    if not rows:
        return "Nothing to summarize: no indexed modules matched."

    # Deterministic pre-flight ALWAYS runs over every file in scope.
    # Previously this only ran when --files was passed, so whole-repo runs
    # printed "no issues found" without ever invoking an analyzer -- a false
    # negative indistinguishable from a clean result.
    target_files = files if files else sorted(scope_files)
    abs_files = [
        os.path.join(idx.root, f)
        for f in target_files
        if os.path.exists(os.path.join(idx.root, f))
    ]
    preflight_ran = bool(abs_files)
    preflight = run_preflight(abs_files) if preflight_ran else ""

    flagged_names, flagged_lines = _parse_flags(preflight)
    for r in rows:
        r["risk"] = risk_score(r, flagged_names, flagged_lines)
    rows.sort(key=lambda r: (r["risk"], r["tok"]), reverse=True)

    out = []
    out.append("# Code Review Summary (lightweight — no full source dump)")
    out.append("")
    out.append(f"- Modules scanned: **{len(modules)}**")
    out.append(f"- Procedures/chunks: **{len(rows)}**")
    out.append(f"- Full-review tokens (all selected): **{total_tok}**")
    out.append("")
    out.append("## Top procedures by RISK (surgical review candidates)")
    out.append("")
    out.append("| # | procedure | kind | lines | tokens | cx | risk |")
    out.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows[:top_n], 1):
        out.append(
            f"| {i} | `{r['module']}.{r['name']}` | {r['kind']} | "
            f"{r['end'] - r['start'] + 1} | {r['tok']} | {r['cx']} | {r['risk']:.0f} |"
        )
    out.append("")

    # Token outlook: proof the summary tier actually saves tokens.
    top5_tok = sum(r["tok"] for r in rows[:5])
    report_tok = estimate("\n".join(out)) + estimate(preflight)
    out.append("## Token outlook")
    out.append("")
    out.append(f"- This summary report: **~{report_tok}** tokens")
    out.append(f"- Surgical review of top-5 hotspots: **~{top5_tok}** tokens")
    out.append(f"- Full dump of everything: **{total_tok}** tokens")
    if total_tok:
        saved = 100 * (1 - (report_tok + top5_tok) / total_tok)
        out.append(f"- **Net saving with summary + surgical review: ~{saved:.0f}%**")
    out.append("")

    out.append("## Deterministic pre-flight (static checks)")
    out.append("")
    if not preflight_ran:
        out.append(
            "**NOT RUN** — no readable files resolved under the repo root. "
            "This is NOT a clean result; do not treat it as one."
        )
    elif preflight.strip():
        out.append(preflight)
    else:
        out.append(f"Ran over {len(abs_files)} file(s): no issues found.")
    out.append("")

    out.append("## Recommended next step")
    out.append("")
    if rows:
        top = rows[0]
        changed = files[0] if files else "<file>"
        out.append(
            "Review the largest/most-complex procedure surgically instead of "
            "the whole module:"
        )
        out.append("```")
        out.append(
            f"python -m crl.cli review <repo> --changed {changed} "
            f"--procedure {top['name']}"
        )
        out.append("```")
    return "\n".join(out)
