"""Tool-level token-savings benchmark (v7 P3).

Measures BEFORE/AFTER chars + est tokens (chars/4, provider-agnostic) for each
compression surface on representative samples. Deterministic, stdlib-only.

Honest scope: this measures the TOOLS, not an end-to-end agent session.
Agent-level savings (rules actually being followed in WorkBuddy / Hermes /
a DeepSeek harness) are a separate verification that needs each target runtime.

Run:
    python3 run_bench.py            # full report + writes REPORT.md
    python3 run_bench.py --check    # compare against BASELINE.json, exit 1 on regression
"""
import argparse
import json
import os
import sys

import tasks

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "token-savings", "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from toks import boot, compress, dedup, mdnorm, astrip, output  # noqa: E402

if not boot.skill_dir():
    sys.exit("toks: cannot locate skill dir (run from repo root or set TOKS_SKILL_DIR)")


def est(text):
    return len(text) // 4


def row(name, sample, before, after):
    return {
        "surface": name,
        "sample": sample,
        "before_chars": len(before),
        "after_chars": len(after),
        "saved_pct": round(100.0 * (len(before) - len(after)) / len(before), 1)
        if before else 0.0,
        "before_tok_est": len(before) // 4,
        "after_tok_est": len(after) // 4,
    }


def run():
    results = []

    # 1. dedup on repeated file read (session: 2nd read returns a ref)
    dc = dedup.DedupCache()
    dc.ref(tasks.CONFIG_REPEAT)                   # prime cache (first read -> keep full)
    second = dc.ref(tasks.CONFIG_REPEAT)         # ref
    results.append({
        "surface": "dedup (file-hash)",
        "sample": "config re-read (2nd read)",
        "before_chars": len(tasks.CONFIG_REPEAT),
        "after_chars": len(second or tasks.CONFIG_REPEAT),
        "saved_pct": round(100.0 * (len(tasks.CONFIG_REPEAT) - len(second)) / len(tasks.CONFIG_REPEAT), 1),
        "before_tok_est": len(tasks.CONFIG_REPEAT) // 4,
        "after_tok_est": len(second) // 4,
    })

    # 2. compress_json
    raw = json.dumps(tasks.BIG_JSON, ensure_ascii=False)
    out = compress.compress_json(tasks.BIG_JSON)
    results.append(row("compress_json", "500-item API payload (nulls+debug)", raw, out))

    # 3. astrip code skeleton
    out = astrip.astrip(tasks.CODE_MODULE, lang="py")
    results.append(row("astrip", "~150-line Python module", tasks.CODE_MODULE, out))

    # 4. trim_bash
    out = compress.trim_bash(tasks.BUILD_LOG, max_lines=40)
    results.append(row("trim_bash", "build log w/ ANSI + repeats", tasks.BUILD_LOG, out))

    # 5. summarize_grep
    out = compress.summarize_grep(tasks.GREP_DUMP, top=10)
    results.append(row("summarize_grep", "150 grep hits", tasks.GREP_DUMP, out))

    # 6. mdnorm HTML -> MD
    out = mdnorm.html_to_markdown(tasks.HTML_PAGE)
    results.append(row("mdnorm", "120-paragraph docs page", tasks.HTML_PAGE, out))

    # 7. O-1 data-only vs prose reply
    prose = tasks.CHAT_REPLY
    data = output.table_lines(["subject", "action"], [["db_schema", "add index on user_id"]])
    results.append(row("O-1 data-only", "chat reply -> table", prose, data))

    return results


def render(results):
    lines = [
        "# Tool-level token-savings benchmark (v7 P3)",
        "",
        "_Deterministic, stdlib-only, provider-agnostic (est tokens = chars/4). "
        "Measures the TOOLS on representative samples — NOT an end-to-end agent "
        "session. Agent-level savings on each target runtime (WorkBuddy / Hermes / "
        "DeepSeek harness) are a separate verification pending that runtime._",
        "",
        "| Surface | Sample | Before chars | After chars | Saved % | Est tok before | Est tok after |",
        "|---------|--------|-------------|-------------|---------|----------------|---------------|",
    ]
    total_b = total_a = 0
    for r in results:
        total_b += r["before_chars"]
        total_a += r["after_chars"]
        lines.append(
            f"| {r['surface']} | {r['sample']} | {r['before_chars']} | "
            f"{r['after_chars']} | {r['saved_pct']}% | "
            f"{r['before_tok_est']} | {r['after_tok_est']} |"
        )
    lines.append("")
    lines.append(f"**Aggregate across samples: {total_b:,} -> {total_a:,} chars "
                 f"({round(100.0 * (total_b - total_a) / total_b, 1)}% saved).**")
    return "\n".join(lines)


def check_regression(results, baseline_path=None):
    """Compare results against BASELINE.json. Returns (passed: bool, report: str)."""
    if baseline_path is None:
        baseline_path = os.path.join(HERE, "BASELINE.json")
    with open(baseline_path, "r", encoding="utf-8") as fh:
        baseline = json.load(fh)
    threshold = baseline.get("threshold_pct", 5.0)
    failures = []
    lines = ["# Benchmark regression check", ""]
    for r in results:
        surface = r["surface"]
        current = r["saved_pct"]
        expected = baseline["surfaces"].get(surface)
        if expected is None:
            lines.append(f"- {surface}: {current}% (no baseline — skipped)")
            continue
        delta = round(current - expected, 1)
        status = "OK" if delta >= -threshold else "FAIL"
        lines.append(f"- {surface}: {current}% (baseline {expected}%, delta {delta:+.1f}pp) [{status}]")
        if delta < -threshold:
            failures.append(f"{surface}: {current}% < {expected}% -{threshold}pp threshold")
    # Aggregate
    total_b = sum(r["before_chars"] for r in results)
    total_a = sum(r["after_chars"] for r in results)
    agg = round(100.0 * (total_b - total_a) / total_b, 1) if total_b else 0.0
    agg_expected = baseline.get("aggregate")
    if agg_expected is not None:
        delta = round(agg - agg_expected, 1)
        status = "OK" if delta >= -threshold else "FAIL"
        lines.append(f"- AGGREGATE: {agg}% (baseline {agg_expected}%, delta {delta:+.1f}pp) [{status}]")
        if delta < -threshold:
            failures.append(f"aggregate: {agg}% < {agg_expected}% -{threshold}pp")
    lines.append("")
    if failures:
        lines.append("REGRESSION DETECTED:")
        for f in failures:
            lines.append(f"  - {f}")
        return False, "\n".join(lines)
    lines.append(f"All surfaces within +/-{threshold}pp of baseline. PASS.")
    return True, "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Token-savings benchmark")
    parser.add_argument("--check", action="store_true",
                        help="compare against BASELINE.json, exit 1 on regression")
    args = parser.parse_args()

    results = run()
    if args.check:
        passed, report = check_regression(results)
        print(report)
        sys.exit(0 if passed else 1)

    report = render(results)
    print(report)
    with open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    print("\n[wrote REPORT.md]")
