"""Small, locked-down web server for the iPhone web app.

Serves ONLY the files inside one folder (never the program folder), no directory listings.
"""
import functools
import http.server
import socketserver
import ssl
import threading


class _Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".webmanifest": "application/manifest+json",
        ".js": "text/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
    }

    def log_message(self, *args):
        pass

    def list_directory(self, path):
        self.send_error(404, "Not found")
        return None

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class _TlsServer(_Server):
    tls_context = None

    def get_request(self):
        conn, addr = self.socket.accept()
        return self.tls_context.wrap_socket(conn, server_side=True, do_handshake_on_connect=False), addr


def _start(server):
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def serve_http(directory, port):
    handler = functools.partial(_Handler, directory=str(directory))
    return _start(_Server(("", port), handler))


def serve_https(directory, port, cert_path, key_path):
    handler = functools.partial(_Handler, directory=str(directory))
    server = _TlsServer(("", port), handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(cert_path), str(key_path))
    server.tls_context = ctx
    return _start(server)
