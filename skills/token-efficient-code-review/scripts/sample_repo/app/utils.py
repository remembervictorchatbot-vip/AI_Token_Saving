def slugify(name: str) -> str:
    """Normalize a string into a url/key-safe slug."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def current_ts() -> int:
    import time
    return int(time.time())


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def format_money(amount: float) -> str:
    return f"${amount:.2f}"


def hash_key(s: str) -> int:
    return sum(ord(c) for c in s) % 1000


def retry(times: int):
    def decorator(fn):
        return fn
    return decorator


def parse_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except ValueError:
        return default


def truncate(text: str, width: int = 80) -> str:
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."
