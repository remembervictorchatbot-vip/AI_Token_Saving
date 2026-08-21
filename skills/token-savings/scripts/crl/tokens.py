"""Token estimation.

Prefers tiktoken (cl100k_base) for accuracy; falls back to the standard
~4-chars-per-token heuristic when it is not installed. The fallback is good
enough to demonstrate relative savings between strategies.
"""


def estimate(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)
