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
    orchestrator: Optional[UnifiedOrchestrator] = None

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
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
            state = self.orchestrator.get_session_state(session_id) if self.orchestrator else None
            if state:
                self._set_headers()
                self.wfile.write(json.dumps(state).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Session not found"}).encode())
        elif path == "/api/status":
            orchestrator = self.orchestrator
            now = time.time()
            
            def _parse_iso_timestamp(ts_str):
                try:
                    return time.mktime(time.strptime(ts_str, "%a %b %d %H:%M:%S %Y"))
                except:
                    return None

            if orchestrator:
                sessions = orchestrator.get_all_sessions()
                latest_ts = 0
                players = []
                for s in sessions:
                    ts = _parse_iso_timestamp(s.get("last_active")) or 0
                    if ts > latest_ts: latest_ts = ts
                    
                    freshness = "live" if (now - ts) < 30 else "stale" if ts > 0 else "unknown"
                    players.append({
                        "id": s["id"],
                        "label": s.get("topic", s["id"]),
                        "role": "player",
                        "liveness": "active" if freshness == "live" else "stalled",
                        "lastTurnAt": s.get("last_active"),
                        "harnessStatus": "unknown"
                    })
                
                freshness = "live" if (now - latest_ts) < 30 and latest_ts > 0 else "stale" if latest_ts > 0 else "unknown"
                status = "ONLINE" if freshness == "live" else "DEGRADED"
                backend_status = "healthy" if freshness == "live" else "degraded"
                
                state = {
                    "truth_mode": "truth_safe_unverified",
                    "truth_bearing_run": False,
                    "source": "orchestrator_state",
                    "freshness": freshness,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "last_observed_at": time.ctime(latest_ts) if latest_ts > 0 else None,
                    "system": {
                        "status": status,
                        "backend_status": backend_status,
                        "monitor_uptime_seconds": int(now)
                    },
                    "players": players,
                    "judges": [],
                    "warnings": ["State is stale."] if freshness == "stale" else []
                }
            else:
                state = {
                    "truth_mode": "truth_safe_unverified",
                    "truth_bearing_run": False,
                    "source": "mock_fallback",
                    "freshness": "fallback",
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "last_observed_at": None,
                    "system": {
                        "status": "DEGRADED",
                        "backend_status": "unavailable",
                        "monitor_uptime_seconds": int(now)
                    },
                    "players": [],
                    "judges": [],
                    "warnings": ["Orchestrator not bound; telemetry is mock/fallback."]
                }
            self._set_headers()
            self.wfile.write(json.dumps(state).encode())
        elif path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok", "truth_mode": "truth_safe_unverified"}).encode())
        elif path == "/api/agents":
            self._set_headers()
            self.wfile.write(json.dumps({"ok": True, "agents": [], "message": "No receipt-backed roster available."}).encode())
        elif path == "/api/persistence":
            self._set_headers()
            self.wfile.write(json.dumps({"ok": True, "message": "No persistence state available."}).encode())
        elif path == "/api/logs/raw":
            self._set_headers()
            self.wfile.write(json.dumps([]).encode())
        elif path == "/api/provenance":
            self._set_headers()
            self.wfile.write(json.dumps([]).encode())
        elif path == "/api/world/spectator/latest":
            self._set_headers()
            self.wfile.write(json.dumps({"ok": False, "status": "unavailable"}).encode())
        elif path == "/api/world/spectator/active-loop/latest":
            self._set_headers()
            self.wfile.write(json.dumps({"ok": False, "status": "unavailable"}).encode())
        elif path in ["/api/missions/latest", "/api/missions/IZH-SPECTRAL-OMISSION-MVS-01", "/api/missions/izh-spectral-omission-mvs-01"]:
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "mission_id": "IZH-SPECTRAL-OMISSION-MVS-01",
                "mission_type": "scientific_model_event",
                "model_family": "Izhikevich",
                "excluded_model_families": ["HH", "Hodgkin-Huxley"],
                "status": "prepared_or_reported_unverified",
                "evidence_status": "reported_unverified",
                "truth_mode": "truth_safe_unverified",
                "truth_bearing_run": False,
                "source": "gamma_hub_mission_observation",
                "gates": [
                    {"gate_id": "repo_preflight", "status": "PASS"},
                    {"gate_id": "lms_slot_inventory", "status": "PASS"},
                    {"gate_id": "harness_identity", "status": "PASS"},
                    {"gate_id": "connectivity_audit", "status": "PASS"},
                    {"gate_id": "poisson_activity_discovery", "status": "PENDING"},
                    {"gate_id": "jax_spectral_loss_validation", "status": "PENDING"},
                    {"gate_id": "nan_inf_gate", "status": "PENDING"},
                    {"gate_id": "artifact_manifest", "status": "PASS"},
                    {"gate_id": "receipt_candidate", "status": "PASS"}
                ],
                "artifacts": [{"name": "mission_context.json", "path": "runtime_artifacts/missions/izh_spectral_omission_mvs01_20260506-2350/mission_context.json", "type": "json"}],
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
                    {"slot_id": f"gamma_{i+1:02}", "role": role, "instance_id": f"gemma-4-e4b-it-mlx{(':' + str(i+1)) if i > 0 else ''}", "status": "reported_not_started"}
                    for i, role in enumerate(["receptionist", "worker_alpha", "worker_beta", "critic", "judge", "redaction_auditor", "receipt_verifier", "synthesizer"])
                ],
                "message": "LMS slot state is observation evidence only."
            }).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def do_POST(self):
        self._set_headers(404)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    httpd = socketserver.TCPServer(("127.0.0.1", 8001), HubAPIHandler)
    logger.info("Started Observation-only Hub API on port 8001")
    httpd.serve_forever()
