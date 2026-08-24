"""Re-read suppression cache (v11).

The single most common agent-loop waste: re-reading a file that has not
changed since the last read. This module records path -> (size, mtime, hash)
on first sight and answers `check()` with HIT when an unchanged region is
about to be re-read (the caller should reuse the cached content / §ref
instead). Complements DedupCache (content-hash on text you already have):
this one works from the FILESYSTEM side before you even read.

Pure stdlib: os.stat + hashlib. Deterministic given identical mtimes.
"""
import hashlib
import json
import os

CACHE_FILE = ".toks-readcache.json"


class ReadCache:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self._cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as fh:
                    self._cache = json.load(fh)
            except Exception:
                self._cache = {}

    def _save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as fh:
                json.dump(self._cache, fh)
        except OSError:
            pass

    @staticmethod
    def _fingerprint(path: str) -> dict:
        st = os.stat(path)
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return {"size": st.st_size, "mtime": st.st_mtime, "sha": h.hexdigest()}

    def record(self, path: str) -> str:
        """Record a fresh read of path. Returns 'recorded'."""
        fp = self._fingerprint(path)
        prev = self._cache.get(path)
        changed = not prev or prev.get("sha") != fp["sha"]
        self._cache[path] = fp
        self._save()
        return "changed" if changed else "unchanged"

    def check(self, path: str) -> dict:
        """HIT when the file exists and is byte-identical to the last recorded
        read (caller should reuse cached content instead of re-reading).
        Never reads file contents into memory beyond hashing."""
        if not os.path.exists(path):
            return {"verdict": "MISS", "reason": "not-found"}
        prev = self._cache.get(path)
        if not prev:
            return {"verdict": "MISS", "reason": "never-recorded"}
        fp = self._fingerprint(path)
        if fp == prev:
            return {"verdict": "HIT", "reason": "mtime+hash unchanged", "saved_chars_hint": prev["size"]}
        return {"verdict": "MISS", "reason": "changed-since-last-read"}

    def reset(self):
        self._cache = {}
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
            except OSError:
                pass


def format_report(res: dict) -> str:
    if res["verdict"] == "HIT":
        return "READ-CACHE HIT ({}): skip re-read, use §cached ref{}".format(
            res["reason"],
            ", ~{} chars".format(res["saved_chars_hint"]) if res.get("saved_chars_hint") else "")
    return "READ-CACHE MISS ({}): read normally, then `record`".format(res["reason"])
