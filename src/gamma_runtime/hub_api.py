import json
import http.server
import socketserver
import logging
import asyncio
import os
import time
from typing import Optional
from urllib.parse import urlparse, parse_qs
from .orchestrator import UnifiedOrchestrator

logger = logging.getLogger("HubAPI")

class HubAPIHandler(http.server.BaseHTTPRequestHandler):
    """
    Standard Library implementation of the Gamma Hub API.
    Provides zero-dependency REST endpoints for the Dashboard.
    """
    orchestrator: Optional[UnifiedOrchestrator] = None

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Enable CORS for the local dashboard
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "service": "gamma_hub",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing": False,
                "status": "lightweight_ready"
            }).encode())
        elif path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            state = self.orchestrator.get_session_state(session_id) if self.orchestrator else None
            if state:
                self._set_headers()
                self.wfile.write(json.dumps(state).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Session not found"}).encode())
        elif path == "/api/status":
            # Returns the complete state for the dashboard
            state = {
                "system": {
                    "id": "GAMMA-WINDOWS-HOST",
                    "status": "IDLE", # To be linked to scheduler pressure
                    "vram": "unknown", # Mocking for now, will link to scheduler
                    "uptime": "unknown",
                    "heartbeat": time.time(),
                    "boot_epoch": "2026-05-05T00:00:00Z"
                },
                "research": {
                    "pass_network": "14-Node grounded",
                    "active_patch": "lightweight-patch",
                    "omissions": 0
                },
                "sessions": self.orchestrator.get_all_sessions() if self.orchestrator else []
            }
            self._set_headers()
            self.wfile.write(json.dumps(state).encode())
        elif path == "/api/events":
            # Safely appended: return structured events for front
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "local/events.jsonl")
            events = []
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                events.append(json.loads(line))
                            except: pass
            self._set_headers()
            self.wfile.write(json.dumps(events[-100:]).encode()) # Return last 100 events
        elif path == "/api/world/spectator/latest" or path == "/api/world/spectator/active-loop/latest":
            self._set_headers()
            self.wfile.write(json.dumps({
                "endpoint": path,
                "ok": False,
                "truth_mode": "truth_safe_unverified",
                "source": "gamma_hub_lightweight_fallback",
                "status": "unavailable",
                "truth_bearing": False,
                "message": "No live spectator payload is available from this lightweight Hub instance."
            }).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/api/launch":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data)
            
            # Use a wrapper to run the async launch in the current event loop
            # Note: This requires the server to be running in an async context or thread
            session_id = self._launch_sync(params)
            
            self._set_headers(201)
            self.wfile.write(json.dumps({"session_id": session_id}).encode())
        else:
            self._set_headers(404)

    def _launch_sync(self, params):
        # This is a bit tricky with http.server. 
        # In a real async server (FastAPI), this would be clean.
        # Here we assume the orchestrator has an async loop running.
        loop = asyncio.get_event_loop()
        future = asyncio.run_coroutine_threadsafe(
            self.orchestrator.launch_run(
                run_type=params.get("type", "council"),
                topic=params.get("topic", "General Inquiry"),
                **params
            ),
            loop
        )
        return future.result()

class HubAPIServer:
    def __init__(self, orchestrator: UnifiedOrchestrator, port: int = None):
        if port is None:
            from .config import HUB_PORT
            port = HUB_PORT
        self.orchestrator = orchestrator
        self.port = port
        HubAPIHandler.orchestrator = orchestrator

    def start(self):
        # We run the TCPServer in a separate thread to not block the main loop
        import threading
        # Try to bind to localhost, which is usually permitted even in restricted environments
        try:
            server = socketserver.TCPServer(("localhost", self.port), HubAPIHandler)
        except Exception:
            # Fallback to 127.0.0.1 if localhost fails
            server = socketserver.TCPServer(("127.0.0.1", self.port), HubAPIHandler)
        
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        logger.info(f"Hub API listening on http://localhost:{self.port}")
        return server
