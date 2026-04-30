import os
import json
import time
import shutil
from datetime import datetime

class CheckpointManager:
    """
    Manages atomic persistence and resumable state for the Gamma Arena.
    Namespaced to the live game session (game001).
    """
    def __init__(self, root_dir, game_id="game001"):
        self.root_dir = root_dir
        self.game_id = game_id
        self.state_path = os.path.join(root_dir, f"local/{game_id}/arena_runtime_state.json")
        self.ensure_dir()

    def ensure_dir(self):
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)

    def atomic_write(self, data):
        """
        Atomic write: Temp file -> fsync -> rename.
        Ensures no state corruption during crashes.
        """
        tmp_path = self.state_path + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.state_path)
            return True
        except Exception as e:
            print(f"Checkpoint write error: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False

    def load_state(self):
        if not os.path.exists(self.state_path):
            return None
        try:
            with open(self.state_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Checkpoint load error: {e}")
            return None

    def update_checkpoint(self, patch_data=None):
        """
        Snapshot current state and update metadata.
        """
        state = self.load_state()
        if not state:
            return False
            
        if patch_data:
            state.update(patch_data)
            
        state["last_checkpoint_time"] = time.time()
        return self.atomic_write(state)

    def register_boot(self):
        """
        Register a new boot event, distinguishing between FRESH and RESUMED.
        """
        state = self.load_state()
        if not state:
            return False
            
        is_resume = state.get("last_checkpoint_time", 0) > 0
        now = time.time()
        
        boot_event = {
            "type": "RESUMED" if is_resume else "FRESH",
            "timestamp": now
        }
        
        state["boot_history"].append(boot_event)
        if len(state["boot_history"]) > 10:
            state["boot_history"].pop(0)
            
        if is_resume:
            state["last_resume_time"] = now
            state["resume_count"] = state.get("resume_count", 0) + 1
            
        return self.atomic_write(state)
