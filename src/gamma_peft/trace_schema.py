import enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from dataclasses import dataclass

class ConsensusLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNANIMOUS = "unanimous"

class TraceMode(str, enum.Enum):
    DISCOVERY = "Discovery"
    PLAN = "Plan"
    CONSOLIDATION = "Consolidation"
    COUNCIL = "Council"
    SDE = "SDE"

@dataclass
class TraceEntry:
    agent_id: str
    content: str
    round: int
    mode: TraceMode

class Trace(BaseModel):
    node_id: str
    role: str
    mode: TraceMode
    input_context: str
    output: str
    references_dois: List[str] = Field(default_factory=list)
    consensus_level: ConsensusLevel = ConsensusLevel.LOW
