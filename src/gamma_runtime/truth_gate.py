import json
import os
import hashlib
import math
import re
from dataclasses import dataclass
from typing import List, Literal, Any
from pathlib import Path

@dataclass(frozen=True)
class Evidence:
    path: str
    sha256: str

@dataclass(frozen=True)
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

def _reject_special_constants(s: str) -> Any:
    raise ValueError(f"NaN or Infinity sentinel found at parse time: {s}")

def validate_truth_gate_decision(
    decision: TruthGateDecision,
    base_dir: str,
    allow_candidate_chain: bool = False
) -> bool:
    """
    Validates a TruthGateDecision artifact based on the provided rules.
    Returns True if valid, raises ValueError with a reason if invalid.
    """
    base_path = Path(base_dir).resolve()

    def _resolve_and_check_path(rel_path: str) -> Path:
        full_path = (base_path / rel_path).resolve()
        # Check path traversal
        if not str(full_path).startswith(str(base_path) + os.sep) and full_path != base_path:
            raise ValueError(f"Evidence path escapes base_dir: {rel_path}")
        return full_path

    # Runtime Enum validation
    if decision.claim_type not in {"simulation_result", "empirical_observation", "tool_improvement", "rejected_invalid"}:
        raise ValueError(f"Invalid claim_type: {decision.claim_type}")
    if decision.truth_status_before not in {"receipt_candidate", "truth_safe_unverified"}:
        raise ValueError(f"Invalid truth_status_before: {decision.truth_status_before}")
    if decision.truth_status_after not in {"truth_value"}:
        raise ValueError(f"Invalid truth_status_after: {decision.truth_status_after}")
    if decision.predecessor_chain_status not in {"verified_truth_chain", "verified_candidate_chain", "blocked_predecessor_not_truth", "blocked_predecessor_missing"}:
        raise ValueError(f"Invalid predecessor_chain_status: {decision.predecessor_chain_status}")

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

    # Verify source files exist and are contained
    for src_file in [decision.source_receipt_candidate, decision.source_artifact_manifest, decision.source_hashes_file]:
        p = _resolve_and_check_path(src_file)
        if not p.exists():
            raise ValueError(f"Required source file missing: {src_file}")

    # 5. truth_status_after checks
    if decision.truth_status_after == "truth_value":
        if not decision.evidence:
            raise ValueError("truth_value promotion requires at least one evidence artifact")

        if decision.predecessor_chain_status in {"blocked_predecessor_not_truth", "blocked_predecessor_missing"}:
             raise ValueError("predecessor_chain_status is blocked, cannot promote to truth_value")

        if decision.predecessor_chain_status == "verified_candidate_chain" and not allow_candidate_chain:
            raise ValueError("Candidate chain policy not enabled. BLOCKED_PREDECESSOR_NOT_TRUTH")

        for ev in decision.evidence:
            # Hash format validation
            if not re.match(r"^[0-9a-fA-F]{64}$", ev.sha256):
                raise ValueError(f"Invalid SHA256 format for {ev.path}")

            full_path = _resolve_and_check_path(ev.path)
            if not full_path.exists():
                raise ValueError(f"Evidence path missing: {ev.path}")

            with open(full_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            if actual_hash != ev.sha256:
                raise ValueError(f"Hash mismatch for {ev.path}")

            if ev.path.endswith(".json"):
                with open(full_path, "r") as f:
                    try:
                        data = json.load(f, parse_constant=_reject_special_constants)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON format: {ev.path} ({e})")
                    except ValueError as e:
                        raise ValueError(f"Parse error in {ev.path}: {e}")

                    if not check_dict_for_invalid(data):
                        raise ValueError(f"NaN or Infinity sentinel found in JSON recursive check: {ev.path}")

    # 7. n4_unblocked true only if next numerical-growth planning and only if valid
    if decision.n4_unblocked:
        if decision.biological_claims_accepted:
             raise ValueError("n4_unblocked cannot be true if biological_claims_accepted is true")
        if decision.truth_status_after != "truth_value":
             raise ValueError("n4_unblocked cannot be true if not promoted to truth_value")

    # 8. Check source receipt candidate for truth_mutation_requested
    full_receipt_path = _resolve_and_check_path(decision.source_receipt_candidate)
    if full_receipt_path.exists():
        with open(full_receipt_path, "r") as f:
            try:
                rc_data = json.load(f, parse_constant=_reject_special_constants)
            except (json.JSONDecodeError, ValueError):
                rc_data = {} # Already handled in evidence validation if it is part of evidence

            if rc_data.get("truth_mutation_requested", False) is True:
                raise ValueError("Source receipt candidate has truth_mutation_requested: true")

    return True
