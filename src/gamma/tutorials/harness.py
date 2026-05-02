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

    def generate_evaluation(self, decision: str, notes: str):
        eval_doc = {
            "run_id": self.run_id,
            "tutorial_id": self.tutorial_id,
            "decision": decision,
            "notes": notes,
            "timestamp": time.time()
        }
        return self.write_artifact("evaluation_decision.json", eval_doc)
