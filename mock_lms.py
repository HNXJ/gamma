import http.server
import json
import socketserver

PORT = 1234

class MockLMSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/v1/models':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            models = {
                "data": [
                    {"id": "G01-builder"},
                    {"id": "G02-tuner"},
                    {"id": "G03-analyst"},
                    {"id": "J01-judge"},
                    {"id": "M01-monitor"}
                ]
            }
            self.wfile.write(json.dumps(models).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/v1/chat/completions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            model = data.get('model', 'unknown')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            reflection = f"Reflection from {model}: Sequential processing verified. Logic is stable."
            updated_state = f"Updated State from {model}: Stack advanced. Ready for next agent."
            
            response = {
                "choices": [{
                    "message": {
                        "content": f"Reflection: {reflection}\nUpdated State: {updated_state}"
                    }
                }]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), MockLMSHandler) as httpd:
    print(f"Mock LMS serving at port {PORT}")
    httpd.serve_forever()
