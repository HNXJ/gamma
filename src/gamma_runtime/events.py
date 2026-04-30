import json
import time
import os
from datetime import datetime

class EventEmitter:
    """
    Structured event emission for the Gamma Arena.
    Writes events to a central log for the frontend to consume.
    """
    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def emit(self, agent_id: str, role: str, event_type: str, summary: str, artifact_path: str = None, status: str = "OK"):
        event = {
            "timestamp": datetime.now().isoformat(),
            "run_id": f"run-{int(time.time())}",
            "agent_id": agent_id,
            "role": role,
            "event_type": event_type,
            "summary": summary,
            "artifact_path": artifact_path,
            "status": status
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
        return event

# Event Schema for Front Streaming:
# {
#   "timestamp": "ISO8601",
#   "run_id": "string",
#   "agent_id": "string",
#   "role": "string",
#   "event_type": "turn_start | message_received | patch_applied | simulation_started | simulation_finished | metrics_recorded | judge_pass | judge_fail | inventory_updated",
#   "summary": "string",
#   "artifact_path": "string",
#   "status": "OK | ERROR"
# }

