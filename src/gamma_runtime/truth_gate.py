import json
import os
import hashlib
import math
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime

@dataclass
class Evidence:
    path: str
    sha256: str

@dataclass
class TruthGateDecision:
    decision_id: str
    source_receipt_candidate: str
    source_artifact_manifest: str
    source_hashes_file: str
    previous_N: int
    accepted_N: int
    claim_type: Literal["simulation_result", "empirical_observation", "tool_improvement", "rejected_invalid"]
    truth_status_before: Literal["receipt_candidate", "truth_safe_unverified"]
    truth_status_after: Literal["truth_value"]
    biological_claims_accepted: bool
    scope: str
    n4_unblocked: bool
    predecessor_chain_status: Literal[
        "verified_truth_chain",
        "verified_candidate_chain",
        "blocked_predecessor_not_truth",
        "blocked_predecessor_missing"
    ]
    evidence: List[Evidence]
    validator_identity: str
    created_at_utc: str

def check_dict_for_invalid(d: Any) -> bool:
    """Recursively check for NaN or Infinity in a dictionary/list representing a JSON object."""
    if isinstance(d, dict):
        for k, v in d.items():
            if not check_dict_for_invalid(v):
                return False
    elif isinstance(d, list):
        for v in d:
            if not check_dict_for_invalid(v):
                return False
    elif isinstance(d, float):
        if math.isnan(d) or math.isinf(d):
            return False
    return True

def validate_truth_gate_decision(
    decision: TruthGateDecision,
    base_dir: str,
    allow_candidate_chain: bool = False
) -> bool:
    """
    Validates a TruthGateDecision artifact based on the provided rules.
    Returns True if valid, raises ValueError with a reason if invalid.
    """
    # 1. biological_claims_accepted must be false for N=3 numerical promotion
    if decision.accepted_N == 3 and decision.biological_claims_accepted:
        raise ValueError("biological_claims_accepted must be false for N=3 numerical promotion")

    # 2. claim_type must remain simulation_result
    if decision.claim_type != "simulation_result":
        raise ValueError("claim_type must be simulation_result")

    # 3. previous_N must equal 2 for this candidate
    if decision.accepted_N == 3 and decision.previous_N != 2:
        raise ValueError("previous_N must be 2 for N=3 candidate")

    # 4. accepted_N must equal 3 for this candidate
    if decision.previous_N == 2 and decision.accepted_N != 3:
        raise ValueError("accepted_N must be 3 for N=2 -> N=3 candidate")

    # 5. truth_status_after checks
    if decision.truth_status_after == "truth_value":
        if decision.predecessor_chain_status == "blocked_predecessor_not_truth" or decision.predecessor_chain_status == "blocked_predecessor_missing":
             raise ValueError("predecessor_chain_status is blocked, cannot promote to truth_value")
             
        if decision.predecessor_chain_status == "verified_candidate_chain" and not allow_candidate_chain:
            raise ValueError("Candidate chain policy not enabled. BLOCKED_PREDECESSOR_NOT_TRUTH")

        for ev in decision.evidence:
            full_path = os.path.join(base_dir, ev.path)
            if not os.path.exists(full_path):
                raise ValueError(f"Evidence path missing: {ev.path}")
            
            with open(full_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            if actual_hash != ev.sha256:
                raise ValueError(f"Hash mismatch for {ev.path}")
            
            if ev.path.endswith(".json"):
                with open(full_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON format: {ev.path}")
                    if not check_dict_for_invalid(data):
                        raise ValueError(f"NaN or Infinity sentinel found in JSON: {ev.path}")

    # 7. n4_unblocked true only if next numerical-growth planning and only if valid
    if decision.n4_unblocked:
        if decision.biological_claims_accepted:
             raise ValueError("n4_unblocked cannot be true if biological_claims_accepted is true")
        if decision.truth_status_after != "truth_value":
             raise ValueError("n4_unblocked cannot be true if not promoted to truth_value")

    # 8. Check source receipt candidate for truth_mutation_requested
    full_receipt_path = os.path.join(base_dir, decision.source_receipt_candidate)
    if os.path.exists(full_receipt_path):
        with open(full_receipt_path, "r") as f:
            try:
                rc_data = json.load(f)
                if rc_data.get("truth_mutation_requested", False) is True:
                    raise ValueError("Source receipt candidate has truth_mutation_requested: true")
            except json.JSONDecodeError:
                pass # Already handled in evidence validation if it is part of evidence

    return True
