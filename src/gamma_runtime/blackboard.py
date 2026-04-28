import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from .types import AgentId

@dataclass
class BlackboardEntry:
    sender: AgentId
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class Blackboard:
    def __init__(self, topic: str):
        self.topic = topic
        self.entries: List[BlackboardEntry] = []
        self.round: int = 0
        self.consensus_reached: bool = False
        self._lock = asyncio.Lock()

    async def add_entry(self, sender: AgentId, content: str, metadata: Optional[Dict[str, Any]] = None):
        async with self._lock:
            entry = BlackboardEntry(
                sender=sender,
                content=content,
                metadata=metadata or {}
            )
            self.entries.append(entry)
            return entry

    def get_recent_summary(self) -> str:
        if not self.entries:
            return "No previous deliberation."
        # Take last 5 entries as summary
        recent = self.entries[-5:]
        summary = "\n".join([f"{e.sender}: {e.content[:200]}..." for e in recent])
        return summary

    def get_history(self) -> List[BlackboardEntry]:
        return list(self.entries)
