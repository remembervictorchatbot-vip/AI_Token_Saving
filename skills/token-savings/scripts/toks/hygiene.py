"""Context hygiene checks (tab/context discipline).

Behavioral complement to compression: keeping the working surface small beats
manual prompt compression. Flags oversized files and reminds on thread cadence.
"""
import os

MAX_LINES = 300
FRESH_THREAD_MIN = 8
FRESH_THREAD_MAX = 10


def file_line_count(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return -1


def hygiene_report(path: str = None, lines: int = None) -> dict:
    n = lines if lines is not None else (file_line_count(path) if path else -1)
    return {
        "lines": n,
        "over_limit": (n > MAX_LINES) if n >= 0 else None,
        "recommend_split": (n > MAX_LINES) if n >= 0 else False,
        "fresh_thread_every": f"{FRESH_THREAD_MIN}-{FRESH_THREAD_MAX} turns",
        "close_unused_tabs": True,
    }
