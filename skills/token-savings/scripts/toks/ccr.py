"""CCR-style reversible compression cache (v14) — the Headroom idea, native.

Lossy-but-recoverable as the default: whenever toks compresses something
(gate, auto-compress, dedup ref substitution), the ORIGINAL is cached locally
keyed by content hash. `toks retrieve <hash>` returns the verbatim original
on demand — so compression never destroys information, it only defers it.

Storage: ~/.toks/ccr/<hash>.txt (plain files; no DB). Retention: LRU cap
(default 200 entries / 50 MB) + optional TTL days. Cache lives OUTSIDE the
skill dir so it is never committed or synced.

Pure stdlib. The cache is write-on-compress and read-on-demand; a missing
entry is a clean MISS (caller falls back to re-reading the source).
"""
import hashlib
import os
import time

DEFAULT_ROOT = os.path.join(os.path.expanduser("~"), ".toks", "ccr")
DEFAULT_MAX_ENTRIES = 200
DEFAULT_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_TTL_DAYS = 30


def ccr_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


class CCR:
    def __init__(self, root: str = DEFAULT_ROOT,
                 max_entries: int = DEFAULT_MAX_ENTRIES,
                 max_bytes: int = DEFAULT_MAX_BYTES,
                 ttl_days: int = DEFAULT_TTL_DAYS):
        self.root = root
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self.ttl_days = ttl_days

    def _path(self, h: str) -> str:
        return os.path.join(self.root, h + ".txt")

    def store(self, text: str, meta: str = "") -> str:
        """Cache an original. Returns its hash. Idempotent per content."""
        os.makedirs(self.root, exist_ok=True)
        h = ccr_hash(text)
        p = self._path(h)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as fh:
                if meta:
                    fh.write("[meta] {}\n".format(meta))
                fh.write(text)
        self._evict()
        return h

    def retrieve(self, h: str) -> dict:
        """Verbatim original by hash. Clean MISS on absent/expired."""
        p = self._path(h)
        if not os.path.exists(p):
            return {"hit": False, "why": "not in cache"}
        age_days = (time.time() - os.stat(p).st_mtime) / 86400
        if age_days > self.ttl_days:
            try:
                os.remove(p)
            except OSError:
                pass
            return {"hit": False, "why": "expired (>{}d)".format(self.ttl_days)}
        text = open(p, encoding="utf-8").read()
        meta = ""
        if text.startswith("[meta] "):
            meta, _, text = text.partition("\n")
            meta = meta[len("[meta] "):]
        return {"hit": True, "text": text, "meta": meta,
                "chars": len(text), "age_days": round(age_days, 1)}

    def stats(self) -> dict:
        entries = []
        total = 0
        if os.path.isdir(self.root):
            for f in os.listdir(self.root):
                p = os.path.join(self.root, f)
                try:
                    total += os.stat(p).st_size
                    entries.append((os.stat(p).st_mtime, f))
                except OSError:
                    continue
        return {"entries": len(entries), "bytes": total}

    def _evict(self):
        """LRU + TTL + caps. Best-effort; never raises."""
        if not os.path.isdir(self.root):
            return
        now = time.time()
        items = []
        for f in os.listdir(self.root):
            p = os.path.join(self.root, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            if (now - st.st_mtime) / 86400 > self.ttl_days:
                try:
                    os.remove(p)
                except OSError:
                    pass
                continue
            items.append((st.st_mtime, st.st_size, p))
        # TTL pass done above; enforce entry count then byte budget (oldest first)
        items.sort()
        while len(items) > self.max_entries:
            _, _, p = items.pop(0)
            try:
                os.remove(p)
            except OSError:
                pass
        total = sum(sz for _, sz, _ in items)
        while total > self.max_bytes and items:
            _, sz, p = items.pop(0)
            try:
                os.remove(p)
            except OSError:
                pass
            total -= sz


def format_report(res: dict, h: str = "") -> str:
    if res["hit"]:
        return ("[ccr HIT {}] {} chars, {}d old{}\n---\n{}\n---".format(
            h, res["chars"], res["age_days"],
            " ({})".format(res["meta"]) if res["meta"] else "",
            res["text"][:4000] + ("\n…(truncated)" if res["chars"] > 4000 else "")))
    return "[ccr MISS {}] {}".format(h, res.get("why", ""))
