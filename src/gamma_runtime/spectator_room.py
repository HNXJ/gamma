import os
import json
import time
import socket
from datetime import datetime
from .db.supabase_client import SupabaseClientWrapper

class SpectatorRoom:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.state_file = os.path.join(root_dir, "local/run/spectator_room.json")
        self.seed_file = os.path.join(root_dir, "context/pillars/spectator_seed.json")
        self.readme_file = os.path.join(root_dir, "README.md")
        self.db = None
        
        self.canonical_queue = [
            "G01-builder", 
            "G02-tuner", 
            "G03-analyst", 
            "J01-judge", 
            "M01-monitor"
        ]
        self._load_or_init()
        try:
            self.db = SupabaseClientWrapper()
        except Exception as e:
            print(f"WARNING: Supabase client initialization failed: {e}")

    def _load_or_init(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
                if "stack" not in self.state: self.state["stack"] = []
                if "turn_index" not in self.state: self.state["turn_index"] = 0
                if "status" not in self.state: self.state["status"] = "ALIVE"
            except Exception:
                self._initialize_new_state()
        else:
            self._initialize_new_state()
            
        # Automatic Sequence Reconciliation
        if self.db:
            latest_id = self.db.get_latest_sequence_id()
            if latest_id is not None:
                current_idx = self.state.get("turn_index", 0)
                if current_idx <= latest_id:
                    print(f"RECONCILIATION: Resuming from sequence {latest_id + 1} (Local was {current_idx})")
                    self.state["turn_index"] = latest_id + 1
                    self._save()

    def _initialize_new_state(self):
        seed_data = {}
        if os.path.exists(self.seed_file):
            try:
                with open(self.seed_file, 'r') as f:
                    seed_data = json.load(f)
            except Exception as e:
                print(f"ERROR: Failed to load spectator seed: {e}")
            
        queue = seed_data.get("queue_order", self.canonical_queue)
        pinned = seed_data.get("pinned_message", "Gamma Arena Spectator Relay Active")
        stack = seed_data.get("initial_stack", [])
        
        allow_fallback = os.environ.get("ALLOW_README_SEED_FALLBACK", "0") == "1"
        
        if not stack:
            if allow_fallback and os.path.exists(self.readme_file):
                try:
                    with open(self.readme_file, 'r') as f:
                        stack = [f.read()]
                except: 
                    stack = ["Fallback: README read failed"]
            else:
                stack = ["Authoritative Initial Seed (Empty Stack)"]

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
            "last_updated": datetime.now().isoformat(),
            "live_ops": self._load_live_ops()
        }
        self._save()

    def _load_live_ops(self):
        try:
            with open(os.path.join(self.root_dir, "local/run/live_ops_state.json"), "r") as f:
                return json.load(f)
        except Exception:
            return {"airdrops": [], "quests": [], "patches": []}

    def log_telemetry(self, actor_id, role, activity_type, target_id, classification):
        log_entry = {
            "actor_id": actor_id,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "activity_type": activity_type,
            "target_id": target_id,
            "classification": classification
        }
        with open(os.path.join(self.root_dir, "local/run/live_ops_telemetry.jsonl"), "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _save(self):
        self.state["last_updated"] = datetime.now().isoformat()
        # Refresh live ops periodically
        self.state["live_ops"] = self._load_live_ops()
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
        
        self.publish_to_supabase()

    def publish_to_supabase(self):
        """Syncs current state to public observer infrastructure."""
        if not self.db:
            return

        try:
            turn_idx = self.state.get("turn_index", 0)
            
            # 1. Publish Authoritative Snapshot
            snapshot_payload = {
                "sequence_id": turn_idx,
                "schema_version": "1.0.0",
                "truth_label": f"Gamma Arena Turn {turn_idx}",
                "source": "gamma-runtime",
                "readonly": True,
                "degraded": self.state.get("mode") == "DEGRADED",
                "neuron_count": 11,
                "state_blob": self.state,
                "provenance": {
                    "timestamp": datetime.now().isoformat(),
                    "host": socket.gethostname()
                }
            }
            self.db.insert_snapshot(snapshot_payload)
            
            # 2. Update Current Pointer (Singleton)
            current_payload = {
                "snapshot_sequence_id": turn_idx,
                "updated_at": datetime.now().isoformat()
            }
            # Pointer ID is 1 (singleton)
            self.db.update_current_pointer(1, current_payload)

            # 3. Events
            if self.state.get("recent_messages"):
                latest_msg = self.state["recent_messages"][-1]
                event_payload = {
                    "sequence_id": turn_idx,
                    "snapshot_sequence_id": turn_idx,
                    "event_type": "turn_reflection",
                    "source": latest_msg.get("sender", "unknown"),
                    "payload": latest_msg
                }
                self.db.insert_event(event_payload)

        except Exception as e:
            print(f"ERROR: Supabase publication failed: {e}")

    def get_current_speaker(self, available_models):
        queue = self.state.get("queue", self.canonical_queue)
        active_queue = [a for a in queue if any(m in a for m in available_models)]
        self.state["active_agents"] = active_queue
        
        if len(active_queue) < 2:
            self.state["status"] = "WAITING_FOR_PLAYERS"
            self._save()
            return None
        
        self.state["status"] = "ALIVE"
        idx = self.state["turn_index"] % len(active_queue)
        speaker = active_queue[idx]
        return speaker

    def post_turn(self, agent_id, reflection, new_stack_item):
        # --- IDLE RECOVERY JUDGE LOGIC ---
        if agent_id == "HEARTBEAT" and "IDLE_ALERT" in reflection:
            self._trigger_recovery(new_stack_item)
        # ---------------------------------
        
        self.state["recent_messages"].append({
            "sender": agent_id, 
            "content": reflection,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.state["recent_messages"]) > 20:
            self.state["recent_messages"].pop(0)
            
        self.state["stack"].append(new_stack_item)
        if len(self.state["stack"]) > 50:
            self.state["stack"].pop(0)
            
        self.state["pinned_message"] = f"[{agent_id}]: {reflection[:100]}..."
        self.state["turn_index"] += 1
        self._save()

    def _trigger_recovery(self, alert_data):
        """Judge (J01) logic to choose recovery level and assign tasks."""
        duration = alert_data.get("duration", 0)
        level = 1 if duration < 600 else 2 if duration < 1200 else 3
        
        roles = ["G01-builder", "G02-tuner", "G03-analyst", "J01-judge", "M01-monitor"]
        recovery_action = "reactivate_quest" if level == 1 else "microtask_round" if level == 2 else "inject_anomaly"
        
        wake_packet = {
            "quest_id": "Q_CRIT_01",
            "action": recovery_action,
            "level": level,
            "assignments": {r: "evidence_audit" for r in roles}
        }
        
        self.post_turn("J01-judge", f"Recovery Initiated (Level {level})", wake_packet)
        self.log_telemetry("J01-judge", "judge", "idle_recovery_cycle", "none", "exploratory")

    def set_status(self, status):
        self.state["status"] = status
        self._save()

    def get_board(self):
        return self.state

    def get_top_of_stack(self):
        return self.state["stack"][-1] if self.state["stack"] else ""
