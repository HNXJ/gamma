import os
import json
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import asdict

logger = logging.getLogger("TutorialHarness")

class TutorialHarness:
    """
    Base harness for Gamma tutorials.
    Ensures truth-safety by isolating artifacts and enforcing schema compliance.
    """
    def __init__(self, root_dir: str, tutorial_id: str):
        self.root_dir = root_dir
        self.tutorial_id = tutorial_id
        self.run_id = str(uuid.uuid4())
        self.artifact_dir = os.path.join(
            root_dir, "data", "tutorials", "artifacts", tutorial_id, self.run_id
        )
        os.makedirs(self.artifact_dir, exist_ok=True)

    def write_artifact(self, filename: str, content: Any):
        path = os.path.join(self.artifact_dir, filename)
        if isinstance(content, (dict, list)):
            with open(path, "w") as f:
                json.dump(content, f, indent=2)
        elif isinstance(content, str):
            with open(path, "w") as f:
                f.write(content)
        else:
            with open(path, "w") as f:
                f.write(str(content))
        return path

    def generate_run_manifest(self, status: str, mission_config: Dict[str, Any]):
        manifest = {
            "run_id": self.run_id,
            "tutorial_id": self.tutorial_id,
            "timestamp": time.time(),
            "status": status,
            "mission_config": mission_config
        }
        return self.write_artifact("run_manifest.json", manifest)

    def generate_evaluation(self, decision: str, notes: str, v_trace: Any = None, warnings: List[str] = None):
        """
        Generates evaluation_decision.json with mandatory scientific gates.
        Enforces FAIL if simulation was bypassed or produced invalid data.
        """
        forced_fail = False
        fail_reasons = []

        if decision == "PASS":
            # 1. Check if simulation executed (no bypass warning)
            if warnings and any("bypassed" in w.lower() for w in warnings):
                forced_fail = True
                fail_reasons.append("Simulation bypass detected in warnings")

            # 2. Check if v_trace is missing or invalid
            if v_trace is None:
                forced_fail = True
                fail_reasons.append("Voltage trace (v_trace) is missing")
            else:
                import numpy as np
                try:
                    v_trace_arr = np.array(v_trace)
                    if v_trace_arr.size == 0:
                        forced_fail = True
                        fail_reasons.append("Voltage trace is empty")
                    elif np.any(np.isnan(v_trace_arr)):
                        forced_fail = True
                        fail_reasons.append("NaN detected in voltage trace")
                    elif np.any(np.isinf(v_trace_arr)):
                        forced_fail = True
                        fail_reasons.append("Inf detected in voltage trace")
                except Exception as e:
                    forced_fail = True
                    fail_reasons.append(f"Error validating v_trace: {str(e)}")

        if forced_fail:
            decision = "FAIL"
            notes = f"[GATE KICKBACK] Original Decision PASS overridden. Reasons: {'; '.join(fail_reasons)}. Original Notes: {notes}"
            logger.warning(f"Evaluation PASS overridden for {self.run_id}: {notes}")

        eval_doc = {
            "run_id": self.run_id,
            "tutorial_id": self.tutorial_id,
            "decision": decision,
            "notes": notes,
            "timestamp": time.time()
        }
        return self.write_artifact("evaluation_decision.json", eval_doc)
