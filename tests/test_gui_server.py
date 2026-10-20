import json
from urllib.request import Request, urlopen

from citereel.gui.server import start_server


def test_gui_ask_offline_roundtrip() -> None:
    server, url = start_server(port=0)
    try:
        health = json.loads(urlopen(url + "api/health", timeout=5).read().decode())
        assert health["ok"] is True

        req = Request(
            url + "api/ask",
            data=json.dumps(
                {
                    "query": "What is the refund window?",
                    "generator": "offline",
                    "k": 3,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        payload = json.loads(urlopen(req, timeout=10).read().decode())
        run = payload["run"]
        assert run["citations"]
        assert "14" in run["answer"] or any("14" in c["text"] for c in run["retrieved"])
    finally:
        server.shutdown()
