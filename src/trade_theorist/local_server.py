"""Loopback-only, immutable private snapshot. No accounts, browser secrets or file routing."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

from .contracts import ContractError
from .private_bundle import checked_path, load_bundle

MIME = {"index.html": "text/html; charset=utf-8", "style.css": "text/css; charset=utf-8",
        "app.js": "text/javascript; charset=utf-8", "private.js": "text/javascript; charset=utf-8",
        "report.json": "application/json; charset=utf-8", "schema.json": "application/json; charset=utf-8", "favicon.svg": "image/svg+xml"}
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'none'; object-src 'none'"


def validate_binding(host, port):
    if host != "127.0.0.1" or type(port) is not int or not 0 <= port <= 65535:
        raise ContractError("Use literal 127.0.0.1 and a port from 0 to 65535")


class PrivateServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(10)
        return request, address

    def handle_error(self, request, client_address):
        pass  # Never put request, path or credential-bearing payloads into diagnostics.


class Handler(BaseHTTPRequestHandler):
    def parse_request(self):
        if not super().parse_request():
            return False
        # The stdlib normalizes leading double slashes. Preserve exact admission.
        if self.requestline.split()[1] != self.path:
            self.send_error(400)
            return False
        return True

    def version_string(self):
        return "TradeTheorist"

    def log_message(self, *_):
        pass

    def send_error(self, code, message=None, explain=None):
        self.respond(code, b"Request refused.\n", "text/plain; charset=utf-8")

    def respond(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Connection", "close")
        if code == 405:
            self.send_header("Allow", "GET, HEAD")
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            self.wfile.write(body)

    def admitted(self):
        # Duplicate security headers and foreign web origins are rejected, even if
        # one of their values looks local. No CORS or private-network opt-in exists.
        if self.headers.get_all("Host", []) != [self.server.authority]:
            return False
        origins = self.headers.get_all("Origin", [])
        if origins and origins != [self.server.origin]:
            return False
        sites = self.headers.get_all("Sec-Fetch-Site", [])
        if sites and sites not in (["same-origin"], ["none"]):
            return False
        return self.client_address[0] == "127.0.0.1"

    def do_GET(self):
        if not self.admitted():
            return self.send_error(403)
        item = self.server.routes.get(self.path)
        if item is None:
            return self.send_error(404)
        name, body = item
        self.respond(200, body, MIME[name])

    do_HEAD = do_GET

    def reject_method(self):
        self.send_error(405 if self.admitted() else 403)

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_TRACE = do_CONNECT = reject_method


def create_server(data_root, output_root, *, fixture=False, host="127.0.0.1", port=8765):
    validate_binding(host, port)
    bundle = checked_path(output_root, outside_git=True)
    data = checked_path(data_root, outside_git=not fixture)
    if data.is_relative_to(bundle):
        raise ContractError("Bundle root cannot contain the private database")
    report, routes = load_bundle(bundle)
    # Recheck lineage, rights and saved arithmetic at launch, never from requests.
    from .operations_v2 import ReadOnlyV2
    from .export_v2 import build_private
    with ReadOnlyV2(data, synthetic=fixture) as store:
        if build_private(store, as_of=report["generated_at"]) != report:
            raise ContractError("Bundle differs from current verified saved evidence; re-export")
    server = PrivateServer((host, port), Handler)
    server.routes = routes
    server.authority = f"127.0.0.1:{server.server_port}"
    server.origin = "http://" + server.authority
    return server


def serve(data_root, output_root, *, fixture=False, host="127.0.0.1", port=8765):
    with create_server(data_root, output_root, fixture=fixture, host=host, port=port) as server:
        print(json.dumps(dict(status="serving", projection_version=2, url=server.origin + "/",
              stop="Press Ctrl+C in this terminal.", refresh="Export and restart to load new evidence; this process serves a fixed validated snapshot.",
              trust="Private to this computer, not protected from other local processes or the same OS user.")), flush=True)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass
    print("Private observatory stopped.", flush=True)
