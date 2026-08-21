"""Safe-mode classifier: refuse to compress high-risk content.

Compression-induced hallucination happens when errors, stack traces, and secrets
are mangled. Safe mode routes these to 0% compression (pass-through) so the model
never "fixes" a redacted secret or misreads a truncated stack trace.
"""
import re

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|pwd|private[_-]?key|"
    r"bearer|authorization|credential)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{8,}",
    re.MULTILINE,
)
STACK_RE = re.compile(
    r"(?i)(traceback \(most recent call last\)|stack trace|"
    r"\bFile \".*\", line \d+|raised? (?:an )?(?:exception|error)|"
    r"at .*\(\w+\.java:\d+\))",
    re.MULTILINE,
)
ERROR_RE = re.compile(r"(?i)\b(error|exception|failed|fatal|panic|segfault|abort)\b", re.MULTILINE)


def risk_level(text: str) -> str:
    """'unsafe' | 'caution' | 'safe' for compression."""
    if SECRET_RE.search(text) or STACK_RE.search(text):
        return "unsafe"
    if ERROR_RE.search(text):
        return "caution"
    return "safe"


def should_compress(text: str) -> bool:
    """False when safe-mode says pass through (0% compression)."""
    return risk_level(text) != "unsafe"
