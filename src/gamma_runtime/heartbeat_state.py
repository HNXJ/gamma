import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger('HeartbeatState')

class HeartbeatManager:
    def __init__(self, root: Path):
        self.root = root
        self.state_file = root / 'local/heartbeat_stats.json'
        self._ensure_file()

    def _ensure_file(self):
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({"agents": {}, "last_real_task_time": time.time()}, f, indent=2)

    def update_agent(self, agent_id: str, metrics: Dict[str, Any]):
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            state['agents'][agent_id] = {
                "last_heartbeat": datetime.now().isoformat(),
                "last_input_size": metrics.get('input_chars', 0),
                "last_output_size": metrics.get('output_chars', 0),
                "total_prompt_tokens": metrics.get('usage_tokens', {}).get('prompt', 0),
                "total_completion_tokens": metrics.get('usage_tokens', {}).get('completion', 0),
                "last_tool_name": metrics.get('last_tool_name')
            }
            
            # Update last real task time if this wasn't an idle review
            if metrics.get('is_idle_review') != True:
                state['last_real_task_time'] = time.time()

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update heartbeat state: {e}")

    def get_state(self) -> Dict[str, Any]:
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {"agents": {}, "last_real_task_time": time.time()}

    def record_real_activity(self):
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            state['last_real_task_time'] = time.time()
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except: pass
