import json
import http.server
import socketserver
import logging
import asyncio
import os
import time
from typing import Optional, Any, TYPE_CHECKING
from urllib.parse import urlparse, parse_qs

if TYPE_CHECKING:
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
                },
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False
            }
            self._set_headers()
            self.wfile.write(json.dumps(state).encode())
        elif path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok", "truth_mode": "truth_safe_unverified"}).encode())
        elif path == "/api/agents":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "status": "unavailable",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_observation_fallback",
                "agents": [],
                "message": "No receipt-backed live agent roster is available."
            }).encode())
        elif path == "/api/persistence":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "status": "unavailable",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_observation_fallback",
                "persistence": {
                    "checkpoint_available": False,
                    "resume_token_available": False
                },
                "message": "No receipt-backed persistence state is available."
            }).encode())
        elif path == "/api/provenance" or path == "/api/logs/raw":
            self._set_headers()
            self.wfile.write(json.dumps([{
                "content": "No provenance rail available in observation mode.",
                "path": "null://system",
                "truth_mode": "truth_safe_unverified"
            }]).encode())
        elif path.startswith("/api/logs/agent/"):
            self._set_headers()
            self.wfile.write(json.dumps({
                "agent_id": path.split("/")[-1],
                "logs": [],
                "truth_class": "DEGRADED",
                "source": "gamma_hub_observation_fallback"
            }).encode())
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
        elif path == "/api/world/spectator/latest":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": False,
                "status": "unavailable",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_observation_fallback",
                "latest": None,
                "row_count": 0,
                "message": "No receipt-backed spectator state is available."
            }).encode())
        elif path == "/api/world/spectator/active-loop/latest":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": False,
                "status": "unavailable",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_observation_fallback",
                "latest": None,
                "row_count": 0,
                "active_loop": None,
                "message": "No receipt-backed active-loop spectator state is available."
            }).encode())
        elif path == "/api/missions/latest" or path == "/api/missions/izh-spectral-omission-mvs-01":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "mission_id": "IZH-SPECTRAL-OMISSION-MVS-01",
                "mission_type": "scientific_model_event",
                "model_family": "Izhikevich",
                "not_model_family": ["HH", "Hodgkin-Huxley"],
                "status": "prepared_or_reported_unverified",
                "evidence_status": "reported_unverified",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_mission_observation",
                "gates": [],
                "artifacts": ["mission_context.json", "izh_mission_event.json"],
                "message": "Mission observation state is reported from artifacts; no Truth-plane acceptance."
            }).encode())
        elif path == "/api/lms/slots":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "status": "reported_unverified",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_lms_slot_observation",
                "model_key": "gemma-4-e4b-it-mlx",
                "intended_variant": "nightmedia/gemma-4-E4B-it-mxfp4-mlx",
                "vision_false_reported": True,
                "slots": [
                    {"slot_id": f"gamma_{i+1:02}", "role": role, "lms_instance_id": f"gemma-4-e4b-it-mlx{(':' + str(i+1)) if i > 0 else ''}", "status": "reported_not_started"}
                    for i, role in enumerate(['receptionist', 'worker_alpha', 'worker_beta', 'critic', 'judge', 'redaction_auditor', 'receipt_verifier', 'synthesizer'])
                ],
                "message": "LMS slot state is observation evidence only."
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
    def __init__(self, orchestrator: Optional[Any], port: int = None):
        if port is None:
            # We import this locally so it doesn't break if config is missing
            try:
                from .config import HUB_PORT
                port = HUB_PORT
            except ImportError:
                port = 8000
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

if __name__ == "__main__":
    # Added observation fallback startup
    logging.basicConfig(level=logging.INFO)
    server = HubAPIServer(None, port=8001)
    logger.info("Starting isolated observation-only Hub API on port 8001")
    httpd = server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
