import os
import json
import time
from datetime import datetime

class SpectatorRoom:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.state_file = os.path.join(root_dir, "local/run/spectator_room.json")
        self.seed_file = os.path.join(root_dir, "context/pillars/spectator_seed.json")
        self.readme_file = os.path.join(root_dir, "README.md")
        
        # Default queue if seed missing
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
        # 1. Load from seed artifact
        seed_data = {}
        if os.path.exists(self.seed_file):
            try:
                with open(self.seed_file, 'r') as f:
                    seed_data = json.load(f)
            except: pass
            
        queue = seed_data.get("queue_order", self.canonical_queue)
        pinned = seed_data.get("pinned_message", "Gamma Arena Spectator Relay Active")
        stack = seed_data.get("initial_stack", ["Initial Seed"])
        
        # If seed missing and README exists, use as legacy fallback for stack only
        if not stack or stack == ["Initial Seed"]:
            if os.path.exists(self.readme_file):
                try:
                    with open(self.readme_file, 'r') as f:
                        stack = [f.read()]
                except: pass

        self.state = {
            "mode": "SAFE MODE",
            "status": "ALIVE",
            "queue": queue,
            "turn_index": 0,
            "active_agents": [],
            "pinned_message": pinned,
            "recent_messages": [],
            "stack": stack,
            "lobby_topics": seed_data.get("lobby_topics", []),
            "baseline": seed_data.get("world_baseline_summary", ""),
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
        queue = self.state.get("queue", self.canonical_queue)
        active_queue = [a for a in queue if any(m in a for m in available_models)]
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
