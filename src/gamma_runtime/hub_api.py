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

        if path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            if self.orchestrator:
                state = self.orchestrator.get_session_state(session_id)
            else:
                state = None
            if state:
                self._set_headers()
                self.wfile.write(json.dumps(state).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Session not found"}).encode())
        elif path == "/api/status":
            state = {
                "system": {
                    "status": "ONLINE",
                    "monitor_uptime_seconds": int(time.time() - float(time.time() - 3600)),
                    "backend_model_slots_occupied": "0/1",
                    "heartbeat": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                },
                "progression": {
                    "largest_pass_network_neuron_count": 0,
                    "active_patches": ["v1.2.4-hotfix"],
                    "next_unlock_threshold": 40,
                    "truth_class": "DEGRADED",
                    "omissions": 0,
                    "canonical_ladder": "alpha-1"
                },
                "persistence": {
                    "boot_type": "COLD",
                    "freshness": "UNVERIFIED",
                    "resume_count": 0
                },
                "research": {
                    "neuron_count": 0,
                    "pass_network": "14-Node grounded",
                    "active_patch": "v1.2.4-hotfix",
                    "omissions": 0
                }
            }
            self._set_headers()
            self.wfile.write(json.dumps(state).encode())
        elif path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok", "truth_mode": "truth_safe_unverified"}).encode())
        elif path == "/api/agents":
            self._set_headers()
            self.wfile.write(json.dumps([]).encode())
        elif path == "/api/persistence":
            self._set_headers()
            self.wfile.write(json.dumps({
                "boot_type": "COLD",
                "freshness": "UNVERIFIED",
                "resume_count": 0
            }).encode())
        elif path == "/api/provenance" or path == "/api/logs/raw":
            self._set_headers()
            self.wfile.write(json.dumps([{
                "content": "No provenance rail available in observation mode.",
                "path": "null://system"
            }]).encode())
        elif path.startswith("/api/logs/agent/"):
            self._set_headers()
            self.wfile.write(json.dumps({
                "agent_id": path.split("/")[-1],
                "logs": [],
                "truth_class": "DEGRADED",
                "source": None
            }).encode())
        elif path == "/api/events":
            self._set_headers()
            self.wfile.write(json.dumps([]).encode())
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
