from typing import List, Tuple
from .trace_schema import Trace, ConsensusLevel

print("INFO: Initializing Gamma Sample Selector") # print("Initializing Gamma Sample Selector")

class SampleSelector:
    def __init__(self, gold_min_score: float = 0.85, silver_min_score: float = 0.70):
        print(f"DEBUG: SampleSelector initialized with gold_min_score={gold_min_score}, silver_min_score={silver_min_score}")
        self.gold_min_score = gold_min_score
        self.silver_min_score = silver_min_score

    def categorize_trace(self, trace: Trace) -> str:
        print(f"DEBUG: Categorizing trace from node {trace.node_id}") # print(f"Categorizing trace from node {trace.node_id}")
        
        # Gold Criteria: human verified OR (high consensus AND high judge score AND DOI support)
        if trace.human_verified or (
            trace.consensus_level in [ConsensusLevel.HIGH, ConsensusLevel.UNANIMOUS] and 
            trace.judge_score >= self.gold_min_score and 
            trace.doi_support
        ):
            print(f"INFO: Trace {trace.node_id} categorized as GOLD") # print(f"Trace {trace.node_id} categorized as GOLD")
            return "gold"
        
        # Silver Criteria: medium+ consensus and moderate+ judge score
        if (
            trace.consensus_level in [ConsensusLevel.MEDIUM, ConsensusLevel.HIGH, ConsensusLevel.UNANIMOUS] and 
            trace.judge_score >= self.silver_min_score
        ):
            print(f"INFO: Trace {trace.node_id} categorized as SILVER") # print(f"Trace {trace.node_id} categorized as SILVER")
            return "silver"
        
        # Red-flag: anything else (unresolved disagreement, low score, etc.)
        print(f"WARNING: Trace {trace.node_id} categorized as RED-FLAG") # print(f"Trace {trace.node_id} categorized as RED-FLAG")
        return "red-flag"

    def select_training_samples(self, traces: List[Trace]) -> List[Trace]:
        print(f"DEBUG: Processing batch of {len(traces)} traces for training selection") # print(f"Processing batch of {len(traces)} traces for training selection")
        selected = [t for t in traces if self.categorize_trace(t) == "gold"]
        print(f"SUCCESS: Selected {len(selected)} gold samples for consolidation") # print(f"Selected {len(selected)} gold samples for consolidation")
        return selected

print("DEBUG: sample_selector.py module load complete") # print("sample_selector.py module load complete")
