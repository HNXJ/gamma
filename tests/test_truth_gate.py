import os
import json
import hashlib
import pytest
from src.gamma_runtime.truth_gate import (
    TruthGateDecision,
    Evidence,
    validate_truth_gate_decision,
    check_dict_for_invalid
)

@pytest.fixture
def temp_evidence_dir(tmp_path):
    base_dir = tmp_path / "evidence"
    base_dir.mkdir()
    
    # Create valid JSON file
    valid_json_path = base_dir / "valid.json"
    valid_data = {"key": "value", "num": 1.0}
    with open(valid_json_path, "w") as f:
        json.dump(valid_data, f)
        
    valid_hash = hashlib.sha256(open(valid_json_path, "rb").read()).hexdigest()
    
    # Create invalid JSON file (with NaN)
    invalid_json_path = base_dir / "invalid.json"
    with open(invalid_json_path, "w") as f:
        f.write('{"num": NaN}')
        
    invalid_hash = hashlib.sha256(open(invalid_json_path, "rb").read()).hexdigest()
    
    # Create receipt_candidate
    rc_path = base_dir / "receipt.json"
    with open(rc_path, "w") as f:
        json.dump({"truth_mutation_requested": False}, f)
        
    return base_dir, "valid.json", valid_hash, "invalid.json", invalid_hash, "receipt.json"

def get_valid_decision() -> TruthGateDecision:
    return TruthGateDecision(
        decision_id="test_decision_1",
        source_receipt_candidate="receipt.json",
        source_artifact_manifest="manifest.json",
        source_hashes_file="hashes.sha256",
        previous_N=2,
        accepted_N=3,
        claim_type="simulation_result",
        truth_status_before="receipt_candidate",
        truth_status_after="truth_value",
        biological_claims_accepted=False,
        scope="numerical N=3 candidate",
        n4_unblocked=True,
        predecessor_chain_status="verified_truth_chain",
        evidence=[],
        validator_identity="test_validator",
        created_at_utc="2026-05-21T00:00:00Z"
    )

def test_valid_decision_object_passes(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256=valid_hash)]
    decision.source_receipt_candidate = rc_file
    
    assert validate_truth_gate_decision(decision, str(base_dir)) is True

def test_biological_claims_accepted_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256=valid_hash)]
    decision.source_receipt_candidate = rc_file
    decision.biological_claims_accepted = True
    
    with pytest.raises(ValueError, match="biological_claims_accepted must be false"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_previous_n_not_2_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256=valid_hash)]
    decision.source_receipt_candidate = rc_file
    decision.previous_N = 1
    
    with pytest.raises(ValueError, match="previous_N must be 2"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_accepted_n_not_3_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256=valid_hash)]
    decision.source_receipt_candidate = rc_file
    decision.accepted_N = 4
    
    with pytest.raises(ValueError, match="accepted_N must be 3"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_predecessor_chain_status_blocked(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256=valid_hash)]
    decision.source_receipt_candidate = rc_file
    decision.predecessor_chain_status = "blocked_predecessor_not_truth"
    
    with pytest.raises(ValueError, match="predecessor_chain_status is blocked"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_nan_infinity_json_sentinel_rejection(temp_evidence_dir):
    base_dir, _, _, invalid_file, invalid_hash, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=invalid_file, sha256=invalid_hash)]
    decision.source_receipt_candidate = rc_file
    
    with pytest.raises(ValueError, match="NaN or Infinity sentinel found in JSON"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_check_dict_helper_works():
    assert check_dict_for_invalid({"a": 1.0}) is True
    assert check_dict_for_invalid({"a": float('inf')}) is False
    assert check_dict_for_invalid([1.0, 2.0]) is True
    assert check_dict_for_invalid([float('nan')]) is False

def test_missing_evidence_path_fails(temp_evidence_dir):
    base_dir, _, _, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path="does_not_exist.json", sha256="fakehash")]
    decision.source_receipt_candidate = rc_file
    
    with pytest.raises(ValueError, match="Evidence path missing"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_hash_mismatch_fails(temp_evidence_dir):
    base_dir, valid_file, _, _, _, rc_file = temp_evidence_dir
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256="wronghash")]
    decision.source_receipt_candidate = rc_file
    
    with pytest.raises(ValueError, match="Hash mismatch"):
        validate_truth_gate_decision(decision, str(base_dir))
        
def test_truth_mutation_requested_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _ = temp_evidence_dir
    
    rc_path = base_dir / "receipt_mut.json"
    with open(rc_path, "w") as f:
        json.dump({"truth_mutation_requested": True}, f)
        
    decision = get_valid_decision()
    decision.evidence = [Evidence(path=valid_file, sha256=valid_hash)]
    decision.source_receipt_candidate = "receipt_mut.json"
    
    with pytest.raises(ValueError, match="Source receipt candidate has truth_mutation_requested: true"):
        validate_truth_gate_decision(decision, str(base_dir))
