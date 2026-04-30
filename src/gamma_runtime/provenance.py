from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from .types import AgentId, SessionId

@dataclass
class CouncilStreamEvent:
    """Structured event for partial token streaming."""
    agent_id: AgentId
    role: str
    event_type: str  # e.g., "token", "status", "error"
    seq: int
    content_delta: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "event_type": self.event_type,
            "seq": self.seq,
            "content_delta": self.content_delta,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class CouncilExecutionRecord:
    """Structured record of a completed council round or mission."""
    session_id: SessionId
    team_id: str
    topic: str
    round: int
    outputs: Dict[AgentId, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "team_id": self.team_id,
            "topic": self.topic,
            "round": self.round,
            "outputs": self.outputs,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
