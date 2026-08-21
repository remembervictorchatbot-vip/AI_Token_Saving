"""Portable skill-dir resolution (v7).

The toolkit must run from any cwd and any install location. Resolution order:
1. env TOKS_SKILL_DIR (explicit override)
2. env HERMES_SKILL_DIR (Hermes Agent sets this for the active skill)
3. autodetect from this file's location (skill root = dir containing scripts/toks)

A candidate is only accepted if it actually contains scripts/toks, so a stale
or wrong env value falls through to the next option instead of breaking.
"""
import os


def skill_dir() -> str:
    """Return the token-savings skill root, or None if it cannot be located."""
    for env in ("TOKS_SKILL_DIR", "HERMES_SKILL_DIR"):
        d = os.environ.get(env)
        if d and _is_skill_root(d):
            return os.path.abspath(d)
    here = os.path.dirname(os.path.abspath(__file__))  # .../scripts/toks
    d = os.path.dirname(os.path.dirname(here))          # skill root
    if _is_skill_root(d):
        return d
    return None


def scripts_dir() -> str:
    """Return the scripts/ dir for the located skill root."""
    root = skill_dir()
    return os.path.join(root, "scripts") if root else None


def _is_skill_root(d: str) -> bool:
    return os.path.isdir(os.path.join(d, "scripts", "toks"))
