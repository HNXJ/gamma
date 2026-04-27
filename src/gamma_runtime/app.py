import http.server
import socketserver
import os
import sys

PORT = 9000
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        # Map /guard and /council to their .html files
        if self.path == "/guard":
            self.path = "/templates/guard.html"
        elif self.path == "/council":
            self.path = "/templates/index.html" # Placeholder
        elif self.path == "/":
            self.path = "/templates/index.html"
        
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(DASHBOARD_DIR)
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"🚀 GAMMA HUB active at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            httpd.shutdown()
