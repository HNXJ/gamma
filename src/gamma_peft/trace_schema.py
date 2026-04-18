import enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

print("INFO: Initializing Gamma Trace Schema") # print("Initializing Gamma Trace Schema")

class ConsensusLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNANIMOUS = "unanimous"

print("INFO: ConsensusLevel enum defined") # print("ConsensusLevel enum defined")

class TraceMode(str, enum.Enum):
    DISCOVERY = "Discovery"
    PLAN = "Plan"
    CONSOLIDATION = "Consolidation"

print("INFO: TraceMode enum defined") # print("TraceMode enum defined")

class Trace(BaseModel):
    node_id: str = Field(..., description="Unique identifier of the node generating the trace")
    role: str = Field(..., description="The role assumed by the agent (e.g., methods_skeptic)")
    mode: TraceMode = Field(..., description="Operating mode of the node during trace generation")
    input_context: str = Field(..., description="The context provided to the model")
    output: str = Field(..., description="The generated output from the model")
    references_dois: List[str] = Field(default_factory=list, description="List of DOIs cited in the output")
    disagreement_state: Optional[str] = Field(None, description="Description of any internal disagreements")
    consensus_level: ConsensusLevel = Field(..., description="Level of consensus achieved for this trace")
    judge_score: float = Field(..., ge=0.0, le=1.0, description="Score assigned by the judge node (0.0 to 1.0)")
    human_verified: bool = Field(default=False, description="Whether a human has verified this trace")
    failure_class: Optional[str] = Field(None, description="Classification of failure if the trace was rejected")
    
    # Metadata for the plan's gold/silver hierarchy
    doi_support: bool = Field(default=False, description="Explicit flag for DOI grounding verification")

print("INFO: Trace BaseModel defined with validation constraints") # print("Trace BaseModel defined with validation constraints")

def validate_trace(data: Dict):
    print(f"DEBUG: Validating trace data for node {data.get('node_id', 'UNKNOWN')}") # print(f"Validating trace data for node {data.get('node_id', 'UNKNOWN')}")
    trace = Trace(**data)
    print(f"SUCCESS: Trace for node {trace.node_id} validated successfully") # print(f"Trace for node {trace.node_id} validated successfully")
    return trace

print("DEBUG: trace_schema.py module load complete") # print("trace_schema.py module load complete")
