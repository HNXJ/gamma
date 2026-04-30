import os
import json
import time
from datetime import datetime

class SpectatorRoom:
    def __init__(self, root_dir):
        self.state_file = os.path.join(root_dir, "local/run/spectator_room.json")
        self.queue = ["G01-builder", "G02-tuner", "G03-analyst", "J01-judge", "M01-monitor"]
        self.lobby_topics = [
            "What is this game?",
            "What is a valid win state?",
            "What makes a neuron addition biologically valid?",
            "What should spectators always be able to see?",
            "What should safe mode preserve at all costs?",
            "What is the difference between spectator room and game room?"
        ]
        self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "mode": "SAFE MODE",
                "current_topic": self.lobby_topics[0],
                "queue": self.queue,
                "pinned_message": "Welcome to the Spectator Room. The world is in SAFE MODE.",
                "recent_messages": [],
                "player_statuses": {p: "IN_SPECTATOR" for p in self.queue},
                "last_updated": datetime.now().isoformat()
            }
            self._save()

    def _save(self):
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def post_message(self, sender, content, pinned=False):
        if pinned:
            self.state["pinned_message"] = f"[{sender}]: {content}"
        
        self.state["recent_messages"].append({"sender": sender, "content": content})
        if len(self.state["recent_messages"]) > 10:
            self.state["recent_messages"].pop(0)
        self._save()

    def move_player(self, agent_id, to_game):
        self.state["player_statuses"][agent_id] = "IN_GAME" if to_game else "IN_SPECTATOR"
        self._save()

    def get_board(self):
        return self.state
