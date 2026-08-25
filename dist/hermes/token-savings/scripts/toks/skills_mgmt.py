"""Skills-management audit (v12b) — the skills counterpart of tool management.

Skills cost context too: every installed skill contributes its name +
description to the always-loaded skill index, and a loaded SKILL.md body can
be thousands of tokens. Synthesizes current best practice:

- agentskills.io: index = name + description only; description IS the trigger
  (unclear description = skill never fires or fires wrongly); SKILL.md should
  be <500 lines / <5k tokens
- Claude Code community: stale plugin caches load skills TWICE; unused
  plugins are ~5k tokens/turn of pure overhead
- joost.blog: unversioned skills are "cached documentation" — stale copies
  mislead (version field + last_checked detect this)
- OpenAI/Cursor forums: near-duplicate descriptions cause double-loading and
  wrong-skill picks

Commands:
  toks skills-audit --dir ~/.hermes/skills   -> full audit report
  toks skills-index --dir ... [--query ...]  -> compact discovery index /
                                                lite-BM25 search over it
Recommend-only: never deletes/moves anything.
"""
import os
import re

from toks.toolsearch import _terms, _one_liner

MAX_BODY_LINES = 500          # agentskills.io recommendation
MAX_BODY_TOKENS = 5000
STALE_DAYS = 180              # no mtime change in ~6 months => review
MIN_DESC_WORDS = 6            # a usable trigger needs a real sentence


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    fm = {}
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    return fm


def scan_skills(root: str) -> list:
    """Find SKILL.md files; return per-skill metadata."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip archives & hidden dirs
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d != "__pycache__"]
        if "SKILL.md" not in filenames:
            continue
        path = os.path.join(dirpath, "SKILL.md")
        rel = os.path.relpath(path, root)
        name = os.path.basename(dirpath)
        try:
            text = open(path, encoding="utf-8").read()
            st = os.stat(path)
        except OSError:
            continue
        import datetime
        age_days = max(0, (datetime.datetime.now().timestamp() - st.st_mtime) / 86400)
        body_lines = len([ln for ln in text.splitlines() if ln.strip()])
        fm = _frontmatter(text)
        desc = fm.get("description", "")
        out.append({
            "name": fm.get("name") or name,
            "path": rel,
            "desc": _one_liner(desc, 100),
            "desc_words": len(desc.split()),
            "version": fm.get("version", ""),
            "body_lines": body_lines,
            "tok_est": max(1, len(text) // 4),
            "age_days": int(age_days),
        })
    return out


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_issues(skills: list) -> list:
    """Flag: duplicates, vague triggers, oversized bodies, stale, unversioned."""
    issues = []
    # near-duplicate names/descriptions
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            a, b = skills[i], skills[j]
            if a["name"].lower() == b["name"].lower():
                issues.append({"type": "DUPLICATE", "skill": b["name"],
                               "detail": "same name as {} ({})".format(
                                   a["name"], a["path"])})
                continue
            ja = _jaccard(_terms(a["desc"]), _terms(b["desc"]))
            if a["desc"] and b["desc"] and ja >= 0.7:
                issues.append({"type": "NEAR-DUP", "skill": b["name"],
                               "detail": "{:.0%} description overlap with {}".format(
                                   ja, a["name"])})
    for s in skills:
        if s["desc_words"] < MIN_DESC_WORDS:
            issues.append({"type": "VAGUE-TRIGGER", "skill": s["name"],
                           "detail": "description {} words — agent cannot decide when to load".format(s["desc_words"])})
        if s["body_lines"] > MAX_BODY_LINES or s["tok_est"] > MAX_BODY_TOKENS:
            issues.append({"type": "OVERSIZED", "skill": s["name"],
                           "detail": "{} lines / {:,} tok > 500 ln / 5k tok guideline".format(
                               s["body_lines"], s["tok_est"])})
        if s["age_days"] > STALE_DAYS and not s["version"]:
            issues.append({"type": "STALE", "skill": s["name"],
                           "detail": "{} days unchanged, no version field (cached-doc risk)".format(s["age_days"])})
    return issues


def build_index(skills: list) -> str:
    """The progressive-disclosure Layer 1: one line per skill."""
    lines = []
    for s in sorted(skills, key=lambda x: x["name"].lower()):
        lines.append("{} — {}".format(s["name"], s["desc"]))
    return "\n".join(lines)


def search_index(skills: list, query: str, top: int = 5) -> list:
    q = _terms(query)
    scored = []
    for s in skills:
        terms = _terms(s["name"]) | _terms(s["desc"])
        score = sum(1 for t in q if t in terms)
        if score:
            scored.append((score, s["name"]))
    scored.sort(reverse=True)
    return [n for _, n in scored[:top]]


def format_report(root: str, skills: list, issues: list) -> str:
    total_tok = sum(s["tok_est"] for s in skills)
    lines = ["skills audit: {} skills, ~{:,} tok if all bodies loaded".format(
        len(skills), total_tok)]
    by_type = {}
    for i in issues:
        by_type.setdefault(i["type"], []).append(i)
    for t in ("DUPLICATE", "NEAR-DUP", "OVERSIZED", "STALE", "VAGUE-TRIGGER"):
        group = by_type.get(t, [])
        if group:
            lines.append("  [{}] {}: {}".format(
                t, len(group), "; ".join(i["skill"] for i in group[:5])
                + ("…" if len(group) > 5 else "")))
    if not issues:
        lines.append("  no issues found")
    lines.append("index size (Layer 1): ~{} tok".format(
        len(build_index(skills)) // 4))
    lines.append("recommend-only — merge/archive/delete is the owner's action")
    return "\n".join(lines)
