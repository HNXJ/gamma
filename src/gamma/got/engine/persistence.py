import os
import json
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class ArenaPersistence:
    """
    Manages the 'Arena World State' for a namespaced game (e.g., game001).
    Ensures atomic writes and tracks critical scientific milestones.
    """
    def __init__(self, game_id: str = "game001", root_dir: str = "/Users/HN/MLLM/gamma"):
        self.game_id = game_id
        self.root_dir = root_dir
        self.base_path = os.path.join(root_dir, "local", game_id)
        self.state_path = os.path.join(self.base_path, "arena_runtime_state.json")
        
        # Ensure directory structure
        os.makedirs(os.path.join(self.base_path, "checkpoints", "runtime"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "checkpoints", "science"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "checkpoints", "milestones"), exist_ok=True)

        self.state = self._load_initial_state()

    def _load_initial_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default Schema for World State
        return {
            "official_level_metric": "largest_pass_network_neuron_count",
            "largest_pass_network_neuron_count": 10,
            "active_patches": ["arena_1_0_0_base"],
            "staged_patches": [],
            "accepted_streak": 0,
            "mailbox_cursor": 0,
            "boot_history": [],
            "optimizer_state_refs": {},
            "best_known_network": None,
            "last_checkpoint_time": None,
            "last_resume_time": None
        }

    def save_state(self, updates: Optional[Dict[str, Any]] = None):
        """
        Atomic Write with Canonical Backend Gate enforcement.
        """
        # Enforcement: prevent bypass
        if os.environ.get("TRUTH_GATE_ENABLED", "1") == "1":
            caller = os.environ.get("AUTHORITY_TOKEN")
            if caller != "CANONICAL_BACKEND_GATE":
                raise PermissionError("SECURITY VIOLATION: Unauthorized write to TRUTH artifact.")
        
        if updates:
            self.state.update(updates)
        
        self.state["last_checkpoint_time"] = datetime.now().isoformat()
        
        # Atomic persistence pattern
        fd, temp_path = tempfile.mkstemp(dir=self.base_path, suffix=".tmp")
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(self.state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self.state_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def record_boot(self):
        """Records a new boot event in the history."""
        boot_event = {
            "timestamp": datetime.now().isoformat(),
            "type": "RESUME" if self.state.get("last_checkpoint_time") else "FRESH"
        }
        self.state.setdefault("boot_history", []).append(boot_event)
        self.state["last_resume_time"] = boot_event["timestamp"]
        self.save_state()

    def get_state(self) -> Dict[str, Any]:
        return self.state

if __name__ == "__main__":
    # Smoke test for namespaced persistence
    p = ArenaPersistence(game_id="game001", root_dir="/Users/hamednejat/workspace/computational/gamma")
    p.record_boot()
    p.save_state({"largest_pass_network_neuron_count": 12})
    print(f"Arena World State grounded at: {p.state_path}")
