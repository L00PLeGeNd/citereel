from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from citereel.paths import DEMO_DOCS
from citereel.pipeline import ask

_STATIC = Path(__file__).resolve().parent / "static"


class GuiState:
    def __init__(self) -> None:
        self.last_run: dict[str, Any] | None = None


def make_handler(state: GuiState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                self._file(_STATIC / "index.html", "text/html; charset=utf-8")
                return
            if path == "/api/health":
                self._json({"ok": True, "demo_docs": str(DEMO_DOCS)})
                return
            if path == "/api/last":
                self._json({"run": state.last_run})
                return
            self.send_error(404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json({"error": "invalid json"}, status=400)
                return

            if path == "/api/ask":
                self._ask(body)
                return
            self.send_error(404)

        def _ask(self, body: dict[str, Any]) -> None:
            query = str(body.get("query") or "").strip()
            if not query:
                self._json({"error": "query required"}, status=400)
                return
            docs = Path(str(body.get("docs") or DEMO_DOCS))
            generator = str(body.get("generator") or "auto")
            provider = body.get("provider") or None
            model = body.get("model") or None
            try:
                run = ask(
                    query,
                    docs,
                    k=int(body.get("k") or 3),
                    generator=generator,
                    provider=str(provider) if provider else None,
                    model=str(model) if model else None,
                    strict=bool(body.get("strict") or False),
                )
            except Exception as exc:
                self._json({"error": str(exc)}, status=400)
                return
            payload = run.to_dict()
            state.last_run = payload
            self._json({"run": payload})

        def _file(self, path: Path, content_type: str) -> None:
            if not path.is_file():
                self.send_error(404)
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    state = GuiState()
    handler = make_handler(state)
    server = ThreadingHTTPServer((host, port), handler)
    chosen = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://{host}:{chosen}/"
    return server, url
