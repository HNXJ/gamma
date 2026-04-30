import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

class GammaAudit:
    def __init__(self, root: Path):
        self.root = root
        self.files_checked: List[str] = []
        self.evidence: Dict[str, Any] = {}
        self.gaps: List[str] = [
            "active_office_mac_entrypoint",
            "active_branch",
            "lms_multi_slot_routing_contract"
        ]

    def _check_file(self, rel_path: str) -> str:
        full_path = self.root / rel_path
        if rel_path not in self.files_checked:
            self.files_checked.append(rel_path)
        if not full_path.exists():
            return ""
        with open(full_path, "r") as f:
            return f.read()

    def get_git_sha(self) -> str:
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return "unknown"

    def run(self) -> Dict[str, Any]:
        git_sha = self.get_git_sha()
        
        # 1. Orchestration Audit
        # We check both the app-layer dispatch and the orchestrator logic
        council_app_code = self._check_file("src/apps/council_app.py")
        orchestrator_code = self._check_file("src/gamma_runtime/orchestrator.py")
        
        # Local main branch council_app uses batch_run, but we check for sequential loops
        has_batch_run = "scheduler.batch_run" in council_app_code
        has_sequential_loop = "for agent in agents:" in council_app_code and "await" in council_app_code.split("for agent in agents:")[1].split("for")[0]
        
        # In the local main branch, council_app.py actually has:
        # for agent in agents: req = build_request; requests.append(...)
        # results = await self.scheduler.batch_run(requests)
        # So it is parallel-dispatch at the app layer.
        
        app_layer_mode = "parallel" if (has_batch_run and not has_sequential_loop) else "sequential"
        
        self.evidence["orchestration"] = {
            "dispatch_mode": {
                "file": "src/apps/council_app.py",
                "value": app_layer_mode,
                "reason": "batch_run detected without interleaved awaits" if app_layer_mode == "parallel" else "sequential agent loop with await detected"
            },
            "scheduler_capability": {
                "file": "src/gamma_runtime/scheduler.py",
                "value": "batch_run_present" if "def batch_run" in self._check_file("src/gamma_runtime/scheduler.py") else "missing"
            }
        }

        # 2. Streaming Audit (Granular)
        backend_code = self._check_file("src/gamma_runtime/backend_lmstudio.py")
        provenance_code = self._check_file("src/gamma_runtime/provenance.py")
        monitor_code = self._check_file("src/apps/sde_game_monitor.py")
        
        stream_schema = "class CouncilStreamEvent" in provenance_code
        stream_emission = "yield CouncilStreamEvent" in backend_code or "emit_stream_event" in orchestrator_code
        stream_consumption = "structured_events.append" in monitor_code and "pass" not in monitor_code.split("structured_events.append")[0].split("while")[1] # Strict check
        
        # Currently, monitor_code has "structured_events = []" but update_monitor_data has "pass" in the placeholder section
        stream_consumption = False # Explicitly false due to "pass" placeholder in monitor
        
        self.evidence["streaming"] = {
            "backend_config": {
                "file": "src/gamma_runtime/backend_lmstudio.py",
                "value": "stream: True" in backend_code,
                "reason": "Hardcoded stream value in payload"
            }
        }

        # 3. Identity Audit
        # Check if agent_id is passed to backend and if naming rule is enforced
        identity_code = self._check_file("src/gamma_runtime/identity.py")
        request_agent_id_sent = '"user": request.agent_id' in backend_code or '"user":' in backend_code and "agent_id" in backend_code
        
        # 4. Final Verdict
        # PASS only if parallel, streaming, and identity are all grounded
        passed = (app_layer_mode == "parallel") and ("stream: True" in backend_code) and request_agent_id_sent and stream_emission
        
        return {
            "verdict": "PASS" if passed else "FAIL",
            "repo_sha": git_sha,
            "files_checked": self.files_checked,
            "evidence": self.evidence,
            "gaps": self.gaps,
            "topology": {
                "declared_agents": ["G01", "G02", "G03", "J01"], # Placeholder for team registry scan
                "players": 3,
                "judges": 1
            },
            "orchestration": {
                "app_layer_dispatch_mode": app_layer_mode,
                "scheduler_capability_present": "def batch_run" in self._check_file("src/gamma_runtime/scheduler.py"),
                "tool_loop_active": "execute_tool_loop" in council_app_code
            },
            "streaming": {
                "structured_stream_schema_present": stream_schema,
                "structured_stream_emission_present": stream_emission,
                "structured_stream_monitor_consumption_present": stream_consumption,
                "structured_stream_ui_surface_present": False
            },
            "identity": {
                "request_agent_id_sent": request_agent_id_sent,
                "request_session_id_sent": "session_id" in backend_code and '"user":' in backend_code,
                "resolved_model_names_distinct": "resolve_runtime_name" in identity_code
            }
        }

if __name__ == "__main__":
    import sys
    # Find root by looking for GEMINI.md or context/
    current = Path(__file__).resolve()
    root = None
    for parent in current.parents:
        if (parent / "context").exists() or (parent / "GEMINI.md").exists():
            root = parent
            break
    
    if not root:
        print(json.dumps({"error": "Could not find project root"}, indent=2))
        sys.exit(1)
        
    audit = GammaAudit(root)
    print(json.dumps(audit.run(), indent=2))
