"""HTTP API for the lab queue."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.queue import join, take


def serve(host: str, port: int, data_dir: str) -> None:
    queue_path = Path(data_dir) / "queue.txt"

    class Handler(BaseHTTPRequestHandler):

        def respond(self, status: int, body: str) -> None:
            payload = body.encode("utf-8")

            self.send_response(status)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if self.path == "/health":
                self.respond(200, "ok")
            else:
                self.respond(404, "not found")

        def do_POST(self) -> None:
            if self.path == "/join":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 0:
                        raise ValueError("Invalid length")

                    body = self.rfile.read(length)
                    data = json.loads(body.decode("utf-8"))

                    if not isinstance(data, dict):
                        raise ValueError("Invalid JSON")  # noqa: TRY004 - HTTP 400 validation contract

                    ticket = join(queue_path, data.get("name"))

                except (ValueError, TypeError):
                    self.respond(400, "invalid name")
                    return

                self.respond(200, str(ticket))

            elif self.path == "/next":
                try:
                    name = take(queue_path)
                except LookupError:
                    self.respond(404, "empty")
                    return

                self.respond(200, name)

            else:
                self.respond(404, "not found")

    with ThreadingHTTPServer((host, port), Handler) as server:
        server.serve_forever()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
# Docker Compose rebuild test
