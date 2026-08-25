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
    # platform installs (v15): hermes skill, opencode skill, mcp registration
    home = os.path.expanduser("~")
    hermes_skill = os.path.join(home, ".hermes", "skills", "token-savings")
    checks.append({"check": "hermes skill", "status": "ok" if os.path.isdir(hermes_skill) else "warn",
                   "detail": hermes_skill if os.path.isdir(hermes_skill) else "not installed",
                   "fix": "" if os.path.isdir(hermes_skill) else
                   "cp -R dist/hermes/token-savings ~/.hermes/skills/"})
    opencode_skill = os.path.join(home, ".opencode", "skills", "token-savings")
    checks.append({"check": "opencode skill", "status": "ok" if os.path.isdir(opencode_skill) else "warn",
                   "detail": opencode_skill if os.path.isdir(opencode_skill) else "not installed (optional)",
                   "fix": "" if os.path.isdir(opencode_skill) else
                   "cp -R skills/token-savings ~/.opencode/skills/ (optional)"})
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


def setup_block() -> str:
    """Copy-paste autopilot wiring for the current machine (v10: easy apply).

    Prints the exact lines to add to the shell profile so toks is on PATH,
    plus the optional endpoint-filter wiring and the system-prompt step.
    """
    try:
        from toks import boot
        root = boot.skill_dir() or "PATH_TO_SKILL_ROOT"
    except Exception:
        root = "PATH_TO_SKILL_ROOT"
    bin_path = os.path.join(root, "bin")
    lines = [
        "# toks setup - paste into ~/.bashrc or ~/.zshrc (or equivalent)",
        "export PATH=\"{}\":$PATH".format(bin_path),
        "# optional: automatic endpoint compression (input gate at the wire)",
        "export TOKS_UPSTREAM=<model endpoint, e.g. https://api.deepseek.com/v1>",
        "export TOKS_PORT=8090",
        "# then start the filter once:",
        "#   python3 dist/deepseek-harness/toks_filter.py",
        "# and paste dist/system-prompt/token-savings-prompt.md at the TOP of",
        "# your system prompt (rules 1-18; auto-start for any model).",
        "# verify:  toks doctor   (aim: all OK)",
    ]
    return "\n".join(lines)


def write_env(path: str = ".toks.env") -> str:
    """Write a .toks.env template the user can fill in (easy apply)."""
    content = ("# toks filter wiring (fill in your model endpoint)\n"
               "TOKS_UPSTREAM=<model endpoint e.g. https://api.deepseek.com/v1>\n"
               "TOKS_PORT=8090\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path