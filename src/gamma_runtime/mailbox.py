import os
import json
import logging
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger('Mailbox')

class Mailbox:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.announcements_path = os.path.join(root_path, 'announcements')
        self.agents_path = os.path.join(root_path, 'agents')

    def build_agent_input(self, agent_id: str, game_id: str, blackboard_text: str, normal_task_text: str) -> str:
        messages = self.get_unread_messages(agent_id)
        
        if not messages:
            return f"BLACKBOARD:\n{blackboard_text}\n\nTASK:\n{normal_task_text}"
            
        header = "=== INBOX (Priority Messages) ===\n"
        msg_body = ""
        for msg in messages:
            msg_body += f"[{msg.get('type', 'announcement').upper()}] {msg.get('title', 'No Title')}\n{msg['body']}\n---\n"
            self.mark_as_seen(agent_id, msg)
            
        return f"{header}{msg_body}\nBLACKBOARD:\n{blackboard_text}\n\nTASK:\n{normal_task_text}"

    def get_unread_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        unread = []
        
        # 1. Global Announcements
        if os.path.exists(self.announcements_path):
            for f in sorted(os.listdir(self.announcements_path)):
                if f.endswith('.json'):
                    path = os.path.join(self.announcements_path, f)
                    with open(path, 'r') as j:
                        msg = json.load(j)
                        msg['_source'] = 'announcements'
                        msg['_filename'] = f
                        if not self.is_seen(agent_id, msg):
                            unread.append(msg)

        # 2. Agent Specific
        agent_inbox = os.path.join(self.agents_path, agent_id, 'inbox')
        if os.path.exists(agent_inbox):
            for f in sorted(os.listdir(agent_inbox)):
                if f.endswith('.json'):
                    path = os.path.join(agent_inbox, f)
                    with open(path, 'r') as j:
                        msg = json.load(j)
                        msg['_source'] = f'agents/{agent_id}'
                        msg['_filename'] = f
                        unread.append(msg)
                        
        # Sort by priority (default 0)
        unread.sort(key=lambda x: x.get('priority', 0), reverse=True)
        return unread

    def is_seen(self, agent_id: str, msg: Dict[str, Any]) -> bool:
        seen_path = os.path.join(self.agents_path, agent_id, 'seen', msg['_filename'])
        return os.path.exists(seen_path)

    def mark_as_seen(self, agent_id: str, msg: Dict[str, Any]):
        seen_dir = os.path.join(self.agents_path, agent_id, 'seen')
        os.makedirs(seen_dir, exist_ok=True)
        
        # If it was in private inbox, move it to seen
        if 'agents/' in msg.get('_source', ''):
            src_path = os.path.join(self.agents_path, agent_id, 'inbox', msg['_filename'])
            dest_path = os.path.join(seen_dir, msg['_filename'])
            if os.path.exists(src_path):
                os.rename(src_path, dest_path)
        else:
            # For announcements, just touch a file in seen
            dest_path = os.path.join(seen_dir, msg['_filename'])
            with open(dest_path, 'w') as f:
                f.write(json.dumps({"seen_at": time.time()}))
        
        # Log acknowledgment
        ack_path = os.path.join(self.agents_path, agent_id, 'acks.jsonl')
        with open(ack_path, 'a') as f:
            f.write(json.dumps({"msg_id": msg.get('id', msg['_filename']), "timestamp": time.time()}) + "\n")

