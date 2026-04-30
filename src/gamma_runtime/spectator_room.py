import os
import json
import time
from datetime import datetime

class SpectatorRoom:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.state_file = os.path.join(root_dir, "local/run/spectator_room.json")
        self.readme_file = os.path.join(root_dir, "README.md")
        self.canonical_queue = [
            "G01-builder", 
            "G02-tuner", 
            "G03-analyst", 
            "J01-judge", 
            "M01-monitor"
        ]
        self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
                # Ensure new fields exist
                if "stack" not in self.state: self.state["stack"] = []
                if "turn_index" not in self.state: self.state["turn_index"] = 0
                if "status" not in self.state: self.state["status"] = "ALIVE"
            except Exception:
                self._initialize_new_state()
        else:
            self._initialize_new_state()

    def _initialize_new_state(self):
        readme_content = ""
        if os.path.exists(self.readme_file):
            try:
                with open(self.readme_file, 'r') as f:
                    readme_content = f.read()
            except:
                readme_content = "Gamma Arena: Initial Seed"
        
        self.state = {
            "mode": "SAFE MODE",
            "status": "ALIVE",
            "queue": self.canonical_queue,
            "turn_index": 0,
            "active_agents": [],
            "pinned_message": "Welcome to the Spectator Room. Seeded from README.",
            "recent_messages": [],
            "stack": [readme_content] if readme_content else ["Initial Seed"],
            "last_updated": datetime.now().isoformat()
        }
        self._save()

    def _save(self):
        self.state["last_updated"] = datetime.now().isoformat()
        # Create directory if missing
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_current_speaker(self, available_models):
        # available_models is a list of agent_ids present in LMS
        active_queue = [a for a in self.canonical_queue if any(m in a for m in available_models)]
        self.state["active_agents"] = active_queue
        
        if len(active_queue) < 2:
            self.state["status"] = "WAITING_FOR_PLAYERS"
            self._save()
            return None
        
        self.state["status"] = "ALIVE"
        # Map turn_index to current active_queue
        idx = self.state["turn_index"] % len(active_queue)
        speaker = active_queue[idx]
        return speaker

    def post_turn(self, agent_id, reflection, new_stack_item):
        self.state["recent_messages"].append({
            "sender": agent_id, 
            "content": reflection,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.state["recent_messages"]) > 20:
            self.state["recent_messages"].pop(0)
            
        self.state["stack"].append(new_stack_item)
        if len(self.state["stack"]) > 50: # Keep stack manageable
            self.state["stack"].pop(0)
            
        self.state["pinned_message"] = f"[{agent_id}]: {reflection[:100]}..."
        self.state["turn_index"] += 1
        self._save()

    def set_status(self, status):
        self.state["status"] = status
        self._save()

    def get_board(self):
        return self.state

    def get_top_of_stack(self):
        return self.state["stack"][-1] if self.state["stack"] else ""
