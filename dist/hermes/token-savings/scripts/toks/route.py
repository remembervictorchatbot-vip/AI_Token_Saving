"""Model-tier routing preflight (v11).

Before dispatching a task, classify it into the lowest sufficient model tier
(mechanical / pattern-matching / reasoning) using deterministic keyword and
shape heuristics from the model-tier-routing pattern, and estimate the cost
delta vs always using the top tier. Pure stdlib, deterministic.

Tier signals:
  Tier 1 (mechanical): formatting, rename, conversion, templating, exact spec,
      single-file mechanical edit, regex, lint fixes.
  Tier 3 (reasoning): architecture, design, security analysis, novel/complex
      debugging, refactor across modules, performance optimization, tradeoffs.
  Tier 2 (pattern-matching): everything else (default).
"""
import re

TIER1_RE = re.compile(
    r"\b(format|reformat|rename|convert|transpile|template|fill[- ]?in|"
    r"regex|lint|typo|spell|sort|deduplicate|boilerplate)\b", re.I)
TIER3_RE = re.compile(
    r"\b(architect|design\b|security|threat|novel|trade-?off|performance "
    r"optimi[sz]|complex debug|root cause|refactor.*(module|system|across)|"
    r"migrat.*schema|algorithm)\b", re.I)


def classify(task_text: str) -> str:
    t = task_text.lower()
    n_files = len(re.findall(r"\band\b|\bthen\b|,", t))  # crude multi-part signal
    if TIER3_RE.search(t):
        return "reasoning"
    if TIER1_RE.search(t) and n_files < 3:
        return "mechanical"
    return "pattern-matching"


TIER_COST = {"mechanical": 0.25, "pattern-matching": 1.0, "reasoning": 5.0}


def estimate(task_text: str, base_cost_per_task: float = 1.0,
             top_tier: str = "reasoning") -> dict:
    """Cost delta if the task is routed to its lowest sufficient tier instead
    of uniformly running on `top_tier`."""
    tier = classify(task_text)
    routed = TIER_COST[tier] * base_cost_per_task
    uniform = TIER_COST[top_tier] * base_cost_per_task
    return {
        "tier": tier,
        "routed_cost": round(routed, 3),
        "uniform_top_tier_cost": round(uniform, 3),
        "saved_pct": round(100.0 * (uniform - routed) / uniform, 1) if uniform else 0.0,
    }


def format_report(res: dict) -> str:
    return ("model-tier route\n"
            "  tier: {tier}\n"
            "  cost routed vs uniform-{u}: {r} vs {un} ({s}% saved)".format(
                tier=res["tier"], u="top", r=res["routed_cost"],
                un=res["uniform_top_tier_cost"], s=res["saved_pct"]))
