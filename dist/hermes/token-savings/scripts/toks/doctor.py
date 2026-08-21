"""Environment doctor (v10): is auto token-saving actually ON here?

Self-check that reports, per hook point, whether the autopilot wiring is
active in the current environment and the one-liner to fix what is not.
Pure stdlib; never writes, only diagnoses.
"""
import os
import shutil
import socket
import sys


def _port_open(port: int) -> bool:
    s = socket.socket()
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def run_checks() -> list:
    """Return a list of {check, status, detail, fix} entries."""
    checks = []
    checks.append({"check": "python", "status": "ok",
                   "detail": sys.version.split()[0], "fix": ""})
    try:
        from toks import boot
        d = boot.skill_dir()
        checks.append({"check": "toolkit", "status": "ok" if d else "missing",
                       "detail": d or "no skill dir found",
                       "fix": "" if d else "set TOKS_SKILL_DIR or run from the repo"})
    except Exception as e:
        checks.append({"check": "toolkit", "status": "missing",
                       "detail": str(e)[:50], "fix": "add scripts/ to PYTHONPATH"})
    upstream = os.environ.get("TOKS_UPSTREAM", "")
    port = int(os.environ.get("TOKS_PORT", "8090"))
    if upstream and _port_open(port):
        checks.append({"check": "input filter", "status": "ok",
                       "detail": "proxy on :{} -> {}".format(port, upstream), "fix": ""})
    elif upstream:
        checks.append({"check": "input filter", "status": "warn",
                       "detail": "TOKS_UPSTREAM set but nothing listening on :{}".format(port),
                       "fix": "python3 dist/deepseek-harness/toks_filter.py"})
    else:
        checks.append({"check": "input filter", "status": "warn",
                       "detail": "endpoint auto-compression OFF (TOKS_UPSTREAM unset)",
                       "fix": "export TOKS_UPSTREAM=<model endpoint>; run toks_filter.py"})
    onpath = shutil.which("toks")
    checks.append({"check": "toks on PATH", "status": "ok" if onpath else "warn",
                   "detail": onpath or "not on PATH",
                   "fix": "" if onpath else "add skills/token-savings/bin to PATH"})
    return checks


def format_report(checks: list) -> str:
    """Human-readable doctor report."""
    lines = ["toks doctor - autopilot wiring check"]
    ok = 0
    for c in checks:
        mark = {"ok": "OK  ", "warn": "WARN", "missing": "MISS"}[c["status"]]
        if c["status"] == "ok":
            ok += 1
        lines.append("  [{}] {}: {}".format(mark, c["check"], c["detail"]))
        if c["fix"]:
            lines.append("         fix: {}".format(c["fix"]))
    lines.append("  {}/{} checks OK - autopilot is {}".format(
        ok, len(checks), "fully wired" if ok == len(checks) else "partially wired"))
    return "\n".join(lines)