#!/usr/bin/env python3
"""Build the Hermes skill bundle from the source-of-truth skill.

Source:  skills/token-savings/
Target:  dist/hermes/token-savings/

The Hermes SKILL.md is hand-customized (different description, version,
metadata) and is NEVER overwritten. Only scripts/ and bin/toks are synced.

Usage:
    python build_hermes_bundle.py          # regenerate bundle from source
    python build_hermes_bundle.py --check  # exit 1 if bundle is out of sync
"""
import argparse
import hashlib
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(REPO_ROOT, "skills", "token-savings")
DST = os.path.join(REPO_ROOT, "dist", "hermes", "token-savings")

# Directories under scripts/ to sync (relative to scripts/)
SYNC_DIRS = ["toks", "crl", "tests", "sample_repo"]
# Files under scripts/ to sync
SYNC_FILES = ["crl_demo.py"]
# Files under bin/ to sync
SYNC_BIN = ["toks", "toks.bat"]
# Never touch these paths in the target (hand-maintained)
PRESERVE = ["SKILL.md"]


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(base, subdirs, files):
    """Return list of (relative_path, absolute_path) under base."""
    result = []
    skip_dirs = {"__pycache__", ".cache", ".ruff_cache", ".mypy_cache"}
    for d in subdirs:
        dirpath = os.path.join(base, d)
        if not os.path.isdir(dirpath):
            continue
        for root, dirs, filenames in os.walk(dirpath):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fn in filenames:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, base)
                result.append((rel, full))
    for fn in files:
        full = os.path.join(base, fn)
        if os.path.isfile(full):
            result.append((fn, full))
    return result


def sync(src_base, dst_base, subdirs, files, check_only=False):
    """Sync files from src_base to dst_base. Returns list of changed files."""
    changes = []
    src_files = collect_files(src_base, subdirs, files)
    src_rels = {rel for rel, _ in src_files}

    # Copy/update files
    for rel, src_full in src_files:
        dst_full = os.path.join(dst_base, rel)
        os.makedirs(os.path.dirname(dst_full), exist_ok=True)
        if os.path.isfile(dst_full) and file_hash(src_full) == file_hash(dst_full):
            continue
        changes.append(rel)
        if not check_only:
            shutil.copy2(src_full, dst_full)

    # Remove stale files in target that no longer exist in source
    if not check_only:
        for rel, _ in collect_files(dst_base, subdirs, files):
            if rel not in src_rels:
                stale = os.path.join(dst_base, rel)
                os.remove(stale)
                changes.append(f"[removed] {rel}")

    return changes


def main():
    parser = argparse.ArgumentParser(description="Build Hermes token-savings bundle")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if bundle is out of sync with source")
    args = parser.parse_args()

    if not os.path.isdir(SRC):
        print(f"ERROR: source not found: {SRC}", file=sys.stderr)
        sys.exit(2)
    if not os.path.isdir(DST):
        print(f"ERROR: target not found: {DST}", file=sys.stderr)
        sys.exit(2)

    # Sync scripts/
    scripts_changes = sync(
        os.path.join(SRC, "scripts"),
        os.path.join(DST, "scripts"),
        SYNC_DIRS, SYNC_FILES,
        check_only=args.check,
    )

    # Sync bin/
    bin_changes = sync(
        os.path.join(SRC, "bin"),
        os.path.join(DST, "bin"),
        [], SYNC_BIN,
        check_only=args.check,
    )

    all_changes = scripts_changes + bin_changes

    if args.check:
        if all_changes:
            print("DRIFT DETECTED — bundle is out of sync with source:")
            for c in all_changes:
                print(f"  {c}")
            print("\nRun: python build_hermes_bundle.py")
            sys.exit(1)
        print("OK — Hermes bundle is in sync with source.")
        sys.exit(0)

    if all_changes:
        print("Updated files:")
        for c in all_changes:
            print(f"  {c}")
    else:
        print("Bundle already up to date — no changes.")
    print(f"\nPreserved (hand-maintained): {', '.join(PRESERVE)}")


if __name__ == "__main__":
    main()
