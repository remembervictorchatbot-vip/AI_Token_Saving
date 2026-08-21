"""Representative sample inputs for the token-savings benchmark.

Kept deterministic (no network, no randomness) so the bench is reproducible.
Each sample mirrors a real task shape: big JSON, code module, web page,
build log, grep dump, repeated file read, chat reply.
"""

BIG_JSON = {
    "status": "ok",
    "debug": "trace-id-xyz",
    "trace": "internal",
    "items": [
        {"id": i, "name": f"item_{i}", "price": i * 1.5, "meta": None, "log": "x"}
        for i in range(500)
    ],
    "total": 500,
}

CODE_MODULE = (
    "import os\nimport sys\nimport re\nimport json\n"
    "from collections import defaultdict\n\n"
    "class Processor:\n"
    "    def __init__(self, path):\n"
    "        self.path = path\n"
    "        self._cache = defaultdict(list)\n\n"
    "    def load(self):\n"
    "        with open(self.path) as fh:\n"
    "            return json.load(fh)\n\n"
    "    def process(self):\n"
    "        data = self.load()\n"
    "        out = []\n"
    "        for k, v in data.items():\n"
    "            if v is not None:\n"
    "                out.append((k, v))\n"
    "        return out\n\n"
    "    def save(self, rows):\n"
    "        with open(self.path, 'w') as fh:\n"
    "            json.dump(rows, fh)\n"
) * 12  # ~150 lines of realistic module

HTML_PAGE = (
    "<!DOCTYPE html><html><head><title>Docs</title>"
    "<style>body{font-family:sans}</style></head><body>"
    "<nav><a href='/'>Home</a><a href='/docs'>Docs</a></nav>"
    "<header><h1>Installation Guide</h1></header>"
    "<article>"
    + "".join(
        f"<p>Step {i}: run <code>pip install pkg{i}</code> then "
        f"<b>restart</b> the service. See <a href='/s{i}'>details</a>.</p>"
        for i in range(120)
    )
    + "</article><footer>Copyright</footer>"
    "<script>track('pageview')</script></body></html>"
)

BUILD_LOG = "\n".join(
    ([f"Step {i}: compiling..." for i in range(30)]
     + ["\x1b[31mWARN: deprecated API used\x1b[0m"] * 8
     + [f"module_{i}.c compiled" for i in range(40)]) * 2
)

GREP_DUMP = "\n".join(
    f"src/module_{i}.py:{j}: TODO fix" for i in range(30) for j in (10, 20, 30, 40, 50)
)

CONFIG_REPEAT = "\n".join(
    [f"key_{i} = value_{i}" for i in range(60)]
)  # read 3x in one session -> dedup applies on re-reads

KEEP_JSON = (
    '{"status": "ok", "debug": "trace-x", "literal": "[[KEEP]]token_abc_12345[[/KEEP]]", '
    '"items": [' + ",".join('{"id": %d, "meta": null, "log": "x"}' % i for i in range(200)) + "]}"
)  # JSON with a protected zone: compress_json alone would touch it; input-gate keeps [[KEEP]]

CONFIG_REPEAT_DELTA = "\n".join(
    [f"key_{i} = value_{i}" for i in range(60)
     if i not in (15, 37)]
    + ["key_15 = NEW_VALUE_15", "key_37 = NEW_VALUE_37"]
)  # same file after an edit -> dedup --diff emits only the changed lines

CHAT_REPLY = (
    "Thank you for reaching out! I'd be happy to help you with your question. "
    "Let me think about this carefully. The answer to your question about the "
    "database schema is that you should definitely use an index on the user_id "
    "column, as this will improve query performance significantly. "
    "I hope this helps! Let me know if you have any other questions!"
)
