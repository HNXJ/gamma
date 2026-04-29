from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Literal

@dataclass
class ProposalPayload:
    proposal_id: str
    seed_pair: int
    healthy_params: Dict[str, float]
    schiz_params: Dict[str, float]
    rationale: str

@dataclass
class ScientificResult:
    proposal_id: str
    status: Literal["accepted", "rejected", "invalid_proposal", "simulation_error", "pending", "running", "completed"]
    healthy: Dict[str, Any] = field(default_factory=dict)
    schiz: Dict[str, Any] = field(default_factory=dict)
    delta: Dict[str, float] = field(default_factory=dict)
    rejection_reason: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[float] = None

# Status taxonomy for Dashboard
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_INVALID = "invalid_proposal"
STATUS_ERROR = "simulation_error"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
