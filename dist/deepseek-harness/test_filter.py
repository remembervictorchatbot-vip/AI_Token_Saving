"""In-process test for toks_filter: spin a stub upstream + the filter, then assert
that a big repeated JSON blob is compressed, [[KEEP]] survives, and the response
passes through. Stdlib only."""
import json
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, __file__ and __file__ or "")
import toks_filter as F  # noqa: E402


class Stub(BaseHTTPRequestHandler):
    received = None

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        Stub.received = self.rfile.read(n)
        data = b'{"id":"stub","choices":[{"message":{"role":"assistant","content":"ok"}}]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def main():
    stub = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
    F.UPSTREAM = f"http://127.0.0.1:{stub.server_address[1]}/v1"
    threading.Thread(target=stub.serve_forever, daemon=True).start()

    filt = ThreadingHTTPServer(("127.0.0.1", 0), F.Handler)
    port = filt.server_address[1]
    threading.Thread(target=filt.serve_forever, daemon=True).start()

    big_blob = json.dumps({"items": [{"id": i, "name": f"n{i}", "meta": None, "debug": "x"} for i in range(300)]})
    big_blob_2 = big_blob  # exact repeat -> must collapse
    keep = f"keep this literal [[KEEP]]tok_abc_12345[[/KEEP]] safe"

    payload = {
        "model": "deepseek-test",
        "messages": [
            {"role": "user", "content": big_blob},
            {"role": "assistant", "content": "seen it"},
            {"role": "user", "content": big_blob_2},
            {"role": "user", "content": keep},
        ],
    }
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                 data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    body = json.loads(resp.read())
    assert body["choices"][0]["message"]["content"] == "ok", "response not passed through"

    sent = json.loads(Stub.received)
    msgs = sent["messages"]
    assert "debug" not in msgs[0]["content"], "JSON not compressed (debug field survived)"
    assert len(msgs[0]["content"]) < len(big_blob), "JSON not shorter"
    assert msgs[2]["content"].startswith("§ref:"), "repeat blob not collapsed to ref"
    assert "[[KEEP]]tok_abc_12345[[/KEEP]]" in msgs[3]["content"], "KEEP zone altered"

    print("ALL PASS: json compressed, repeat->§ref, KEEP intact, response passthrough")
    stub.shutdown()
    filt.shutdown()


if __name__ == "__main__":
    main()
