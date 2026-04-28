import http.server
import socketserver
import os
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("GAMMA_HUB_PORT", "3012"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
LOG_DIR = os.path.join(BASE_DIR, "local", "logs")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/guard":
            self.path = "/templates/guard.html"
            return super().do_GET()
        if parsed.path == "/council" or parsed.path == "/":
            self.path = "/templates/index.html"
            return super().do_GET()
        if parsed.path == "/log":
            qs = parse_qs(parsed.query)
            name = qs.get("name", ["v1_gamma_mxfp8_council.log"])[0]
            target = os.path.join(LOG_DIR, name)
            if not os.path.exists(target):
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"Log not found: {target}".encode("utf-8"))
                return
            with open(target, "rb") as f:
                data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            return
        return super().do_GET()

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    os.chdir(DASHBOARD_DIR)
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"GAMMA HUB active at http://0.0.0.0:{PORT}")
        httpd.serve_forever()
