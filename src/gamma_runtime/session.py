from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class AgentSession:
    """The lightweight runtime overlay representing an active agent."""
    agent_id: str
    session_id: str = field(default_factory=lambda: str(uuid4()))
    history: list[dict[str, str]] = field(default_factory=list)
    notes: dict = field(default_factory=dict)
    kv_cache_ref: str | None = None

    def push(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
