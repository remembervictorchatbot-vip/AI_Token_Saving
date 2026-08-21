"""Deterministic-first pre-filter: run free static analyzers on changed files
before any LLM semantic review. This is the cheapest accuracy win -- it catches
mechanical issues (lint, type errors, common bug/security patterns) for near-zero
token cost, so the model only spends tokens on genuine semantic problems.

All analyzers are free and open-source. Missing tools are skipped with an install
hint rather than failing the run.
"""

import os
import re
import shutil
import subprocess

from .chunker import looks_like_vba

PROC_DEF_RE = re.compile(
    r'^\s*(?:Public\s+|Private\s+|Friend\s+|Static\s+)*'
    r'(Sub|Function|Property\s+(?:Get|Let|Set))\s+([A-Za-z_]\w*)',
    re.M | re.I,
)
# Any bare `Label:` line. Deciding whether it is an ERROR handler is done
# separately -- an inline `(?:Err|Error|Handler)` sub-pattern can never match
# `ErrH:` because the leading `[A-Za-z_]` consumes the `E`.
LABEL_RE = re.compile(r'^[ \t]*([A-Za-z_]\w*)[ \t]*:[ \t]*\r?$', re.M)
HANDLER_NAME_RE = re.compile(r'err|fail|handler|catch', re.I)

ANALYZERS = {
    "ruff": {
        "bin": "ruff",
        "args": ["check", "--output-format", "concise"],
        "help": "lint + style",
        "install": "pip install ruff",
    },
    "mypy": {
        "bin": "mypy",
        "args": ["--no-error-summary", "--show-column-numbers"],
        "help": "static type check",
        "install": "pip install mypy",
    },
    "semgrep": {
        "bin": "semgrep",
        "args": ["--quiet", "--error", "--no-rewrite-rule-ids"],
        "help": "pattern-based bug/security scan",
        "install": "pip install semgrep",
    },
}


def _resolve(binary):
    """Find the analyzer binary, falling back to the managed venv path."""
    p = shutil.which(binary)
    if p:
        return p
    cand = os.path.join(
        os.path.expanduser("~"),
        ".workbuddy",
        "binaries",
        "python",
        "envs",
        "default",
        "bin",
        binary,
    )
    return cand if os.path.exists(cand) else None


def _code_part(line):
    """Return `line` with any trailing comment removed, honoring `"`-delimited
    string literals. Used so explanatory comments that merely mention a pattern
    (e.g. `On Error Resume Next`, `Like "#"`) are never flagged as live code.
    """
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
            out.append(ch)
        elif ch == "'" and not in_str:
            break
        else:
            out.append(ch)
    return "".join(out)


def lint_vba(text):
    """Free, dependency-free static checks for VBA modules."""
    lines = text.splitlines()
    findings = []

    # 1. Option Explicit at module top
    if not re.search(r'^\s*Option\s+Explicit\b', text, re.M | re.I):
        findings.append("MODULE: Missing `Option Explicit` — undeclared variables fail silently.")

    # 2. Select/Activate / Active* objects (slow + fragile)
    for i, ln in enumerate(lines, 1):
        if re.search(r'\.(?:Select|Activate)\s*\(|\bSelection\.|\bActiveCell\b|\bActiveSheet\b|\bActiveWorkbook\b|\bActiveWindow\b', ln):
            findings.append(f"L{i}: avoid .Select/.Activate/Active* objects — reference objects directly (faster, less fragile).")

    # 3. Hard-coded paths
    for i, ln in enumerate(lines, 1):
        if re.search(r'[A-Za-z]:\\|/Users/|/home/', ln):
            findings.append(f"L{i}: hard-coded path literal — externalize to config.")

    # 4. On Error Resume Next without a later reset (per procedure).
    #    A reset is ANY `On Error GoTo <label>` (incl. `GoTo 0`) — not just `GoTo 0`.
    SAFE_GOTO = {"safeexit", "cleanup", "errh", "retry", "nextrow", "continue", "nexti", "skip",
                 "cleanbatch", "savehashes", "nextbatch", "cleanupfail", "cleanupok", "cleandata"}
    blocks = re.split(r'\n(?=\s*(?:Public\s+|Private\s+|Friend\s+)*(?:Sub|Function|Property)\s)', text)
    for blk in blocks:
        # Strip comments: explanatory prose (e.g. "`On Error Resume Next` ...")
        # must not be mistaken for live error handling in the procedure.
        blk_code = "\n".join(_code_part(l) for l in blk.splitlines())
        if re.search(r'\bOn\s+Error\s+Resume\s+Next\b', blk_code, re.I) and \
           not re.search(r'\bOn\s+Error\s+GoTo\s+\S+', blk_code, re.I):
            m = re.search(r'(?:Sub|Function|Property)\s+([A-Za-z_]\w*)', blk)
            name = m.group(1) if m else "?"
            findings.append(f"PROC {name}: `On Error Resume Next` with no `On Error GoTo` reset — errors silently swallowed for the rest of the procedure.")

    # 5. GoTo to non-handler labels (spaghetti risk). GoTo SafeExit/Cleanup/ErrH
    #    etc. is idiomatic error/early-exit handling and is not flagged.
    for i, ln in enumerate(lines, 1):
        gm = re.match(r'\s*GoTo\s+([A-Za-z_]\w*)', ln)
        if gm and gm.group(1).lower() not in SAFE_GOTO:
            findings.append(f"L{i}: `GoTo {gm.group(1)}` — prefer structured control flow.")

    # 6. Unreferenced procedures (dead code). Counts references in executable
    #    lines AND string literals (VBA dispatches via `Application.Run "Name"`),
    #    but ignores full-line comments -- a procedure that survives only in a
    #    commented-out call site is still dead.
    def _strip_comments(s):
        return "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("'"))

    code_only = _strip_comments(text)
    # Map each procedure to its own block so self-references -- including VBA's
    # `FunctionName = value` return-assignment idiom -- are not counted as uses.
    own_body = {}
    for blk in blocks:
        h = re.match(r'\s*(?:Public\s+|Private\s+|Friend\s+|Static\s+)*'
                     r'(?:Sub|Function|Property\s+(?:Get|Let|Set))\s+([A-Za-z_]\w*)', blk, re.I)
        if h:
            own_body.setdefault(h.group(1), []).append(_strip_comments(blk))
    for m in PROC_DEF_RE.finditer(text):
        name = m.group(2)
        ln = text[:m.start()].count("\n") + 1
        pat = re.compile(r'\b' + re.escape(name) + r'\b', re.I)
        total = len(pat.findall(code_only))
        internal = sum(len(pat.findall(b)) for b in own_body.get(name, []))
        if total - internal <= 0:
            findings.append(
                f"L{ln}: `{name}` is never referenced outside its own body "
                f"— dead code (or a live trap if it is Public and stale)."
            )

    # 7. Inconsistent error propagation. A Sub whose handler logs an error but
    #    does NOT `Err.Raise` returns cleanly to its caller, so a wrapper that
    #    checks Err.Number sees success. Only flagged when OTHER Subs in the
    #    same module DO re-raise -- i.e. this one is the odd one out. Functions
    #    are excluded: returning a sentinel on the error path is a valid contract.
    raisers, swallowers = [], []
    for blk in blocks:
        head = re.match(r'\s*(?:Public\s+|Private\s+|Friend\s+|Static\s+)*(Sub|Function)\s+'
                        r'([A-Za-z_]\w*)\s*\(([^)]*)\)', blk)
        if not head or head.group(1).lower() != "sub":
            continue
        # Zero-arg Public Subs are macro ENTRY POINTS -- they are the top of the
        # call stack and have no caller to propagate to. Not a defect.
        if not head.group(3).strip():
            continue
        hm = next((m for m in LABEL_RE.finditer(blk)
                   if HANDLER_NAME_RE.search(m.group(1))), None)
        if not hm:
            continue
        tail = blk[hm.end():]
        if not re.search(r'\bLog\b|\bDebug\.Print\b|\bMsgBox\b', tail, re.I):
            continue
        line_no = text[:text.find(blk)].count("\n") + 1 if blk in text else 0
        # A Sub propagates the error if it `Err.Raise`s OR if it uses the
        # deferred-relay pattern (StashError in the handler + RethrowIfPending in
        # Cleanup). Both free resources AND propagate the failure to the caller.
        propagates = re.search(
            r'\bErr\.Raise\b|\bStashError\b|\bRethrowIfPending\b', tail
        )
        (raisers if propagates else swallowers).append(
            (head.group(2), line_no)
        )
    if raisers and swallowers:
        for name, ln in swallowers:
            findings.append(
                f"L{ln}: Sub `{name}` logs in its error handler but never "
                f"`Err.Raise`s, while {len(raisers)} sibling Sub(s) do — the "
                f"caller sees SUCCESS after a failed run (silent corruption)."
            )

    # 8. `Like` patterns using `#` (matches exactly ONE digit). Almost always a
    #    bug when the generated names embed dates/counters of varying width.
    #    Comments (full-line AND inline) are stripped first so explanatory text
    #    that merely mentions a `Like "#"` pattern is never flagged.
    for i, ln in enumerate(lines, 1):
        code_ln = _code_part(ln)
        if "Like" not in code_ln:
            continue
        lm = re.search(r'\bLike\b\s*"([^"]*#[^"]*)"', code_ln)
        if lm:
            findings.append(
                f"L{i}: `Like \"{lm.group(1)}\"` — `#` matches exactly ONE digit. "
                f"Multi-digit values (dates, counters) will never match. Use `*`."
            )

    return "\n".join(findings)


def run_preflight(files, analyzers=None):
    """Run deterministic checks over `files`. Returns a markdown-ish block.

    VBA files are linted with the built-in `lint_vba` (no external binaries).
    Other files are run through the free binary analyzers (ruff / mypy / semgrep).
    """
    analyzers = analyzers or list(ANALYZERS.keys())
    sections = []
    vba_files, other_files = [], []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                src = fh.read()
        except Exception:
            other_files.append(f)
            continue
        if looks_like_vba(src):
            vba_files.append((f, src))
        else:
            other_files.append(f)

    # VBA deterministic lint (no binaries required)
    for f, src in vba_files:
        res = lint_vba(src)
        if res.strip():
            sections.append(f"## vba-lint ({os.path.basename(f)})\n```\n{res.strip()}\n```")
        else:
            sections.append(f"## vba-lint ({os.path.basename(f)})\n  No common VBA issues found.")

    # Binary analyzers on non-VBA files
    if other_files:
        for name in analyzers:
            spec = ANALYZERS.get(name)
            if not spec:
                continue
            bin_path = _resolve(spec["bin"])
            if not bin_path:
                sections.append(
                    f"## {name} (SKIPPED: not installed)\n"
                    f"  Free + local. Install: `{spec['install']}`"
                )
                continue
            try:
                proc = subprocess.run(
                    [bin_path, *spec["args"], *other_files],
                    capture_output=True, text=True, timeout=120,
                )
            except subprocess.TimeoutExpired:
                sections.append(f"## {name}\n  TIMEOUT after 120s")
                continue
            out = (proc.stdout or "") + (proc.stderr or "")
            if not out.strip():
                sections.append(f"## {name}\n  No issues found.")
            else:
                sections.append(f"## {name} ({spec['help']})\n```\n{out.strip()}\n```")
    return "\n\n".join(sections)
