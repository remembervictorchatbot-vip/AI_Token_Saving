"""O-6 validate-then-emit gate - generalized from the O-1 JSON gate (new, v8).

Pure stdlib, deterministic. Python uses compile(); JSON uses json.loads();
Markdown checks balanced code fences.
"""
import json


def validate(text: str, lang: str = "py") -> tuple:
    """Return (ok: bool, message: str) - the O-6 gate for an artifact."""
    if lang == "json":
        try:
            json.loads(text)
            return True, "VALID"
        except Exception as e:
            return False, f"INVALID: {e}"
    if lang == "md":
        fences = text.count("```")
        if fences % 2 != 0:
            return False, f"INVALID: unbalanced code fences ({fences})"
        return True, "VALID"
    # default: python syntax
    try:
        compile(text, "<toks>", "exec")
        return True, "VALID"
    except SyntaxError as e:
        return False, f"INVALID: line {e.lineno}: {e.msg}"