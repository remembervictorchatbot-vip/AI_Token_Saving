"""Content-hash dedup with short reference substitution (sqz pattern).

Usage model for the assistant:
- Before injecting the same file / tool output / URL body a SECOND time, call
  DedupCache().ref(content).
- If it returns None  -> first occurrence, keep the full content.
- If it returns "§ref:HASH§" -> it is a duplicate; substitute the ref token
  instead of re-pasting. The original remains recoverable (re-read / source).
"""
import difflib
import hashlib
import json
import os
from typing import Dict, Optional

REF_OPEN = "\u00a7ref:"   # §ref:
REF_CLOSE = "\u00a7"      # §
DIFF_OPEN = "\u00a7diff:"  # §diff: (delta re-read, v8)
DIFF_CLOSE = "\u00a7"      # §

DEFAULT_CACHE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".cache", "dedup.json"
)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def is_ref(token: str) -> Optional[str]:
    if (
        isinstance(token, str)
        and token.startswith(REF_OPEN)
        and token.endswith(REF_CLOSE)
        and len(token) > len(REF_OPEN) + len(REF_CLOSE)
    ):
        return token[len(REF_OPEN):-len(REF_CLOSE)]
    return None


class DedupCache:
    def __init__(self, cache_path: str = DEFAULT_CACHE):
        self.cache_path = cache_path
        self.store: Dict[str, dict] = self._load()
        self.latest = self.store.get("_latest")   # last seen content (for diff)
        self.hits = 0
        self.stored = 0

    def _load(self) -> Dict[str, dict]:
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        data = dict(self.store)
        if self.latest is not None:
            data["_latest"] = self.latest
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def ref(self, content: str) -> Optional[str]:
        """Return ref token if already seen (substitute it); else None (keep full)."""
        h = content_hash(content)
        if h in self.store:
            self.hits += 1
            return f"{REF_OPEN}{h}{REF_CLOSE}"
        self.store[h] = {
            "hash": h,
            "len": len(content),
            "preview": content[:80].replace("\n", " "),
        }
        self.latest = {"hash": h, "content": content}
        self.stored += 1
        self._save()
        return None

    def diff_ref(self, content: str) -> Optional[str]:
        """Delta-aware re-read (v8): returns None on first sight, a \u00a7ref:\u00a7
        token on an exact repeat, or a \u00a7diff:\u00a7 header + changed-line hunks
        when the content CHANGED since the last sight (unchanged parts stay cached
        and are JIT-expandable; only the delta crosses the wire)."""
        h = content_hash(content)
        if h in self.store:
            return f"{REF_OPEN}{h}{REF_CLOSE}"
        prev = self.latest
        if prev is not None and content != prev.get("content"):
            diff = "".join(difflib.unified_diff(
                prev["content"].splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile="cached", tofile="current", n=0,
            ))
            header = (DIFF_OPEN + h + DIFF_CLOSE + " (delta vs "
                      + REF_OPEN + prev["hash"] + REF_CLOSE + ")")
            self.store[h] = {
                "hash": h,
                "len": len(content),
                "preview": content[:80].replace("\n", " "),
            }
            self.latest = {"hash": h, "content": content}
            self.stored += 1
            self._save()
            return header + "\n" + diff
        self.store[h] = {
            "hash": h,
            "len": len(content),
            "preview": content[:80].replace("\n", " "),
        }
        self.latest = {"hash": h, "content": content}
        self.stored += 1
        self._save()
        return None

    def expand(self, ref_token: str) -> Optional[str]:
        h = is_ref(ref_token)
        if h is None:
            return None
        return self.store.get(h, {}).get("preview")

    def stats(self) -> dict:
        n = len([k for k in self.store if k != "_latest"])
        return {"entries": n, "hits": self.hits, "stored": self.stored,
                "latest": (self.latest or {}).get("hash")}

    def reset(self) -> None:
        self.store = {}
        self.latest = None
        self.hits = 0
        self.stored = 0
        self._save()
