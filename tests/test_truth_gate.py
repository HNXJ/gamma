import os
import json
import hashlib
import pytest
from dataclasses import replace
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

    # Create required source files
    rc_path = base_dir / "receipt.json"
    with open(rc_path, "w") as f:
        json.dump({"truth_mutation_requested": False}, f)

    manifest_path = base_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({}, f)

    hashes_path = base_dir / "hashes.sha256"
    with open(hashes_path, "w") as f:
        f.write("")

    return base_dir, "valid.json", valid_hash, "invalid.json", invalid_hash, "receipt.json", "manifest.json", "hashes.sha256"

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
        evidence=[Evidence(path="valid.json", sha256="PLACEHOLDER")], # placeholder hash will be replaced in tests
        validator_identity="test_validator",
        created_at_utc="2026-05-21T00:00:00Z"
    )

def test_valid_decision_object_passes(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(), evidence=[Evidence(path=valid_file, sha256=valid_hash)])
    assert validate_truth_gate_decision(decision, str(base_dir)) is True

def test_biological_claims_accepted_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       biological_claims_accepted=True)
    with pytest.raises(ValueError, match="biological_claims_accepted must be false"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_previous_n_not_2_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       previous_N=1)
    with pytest.raises(ValueError, match="previous_N must be 2"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_accepted_n_not_3_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       accepted_N=4)
    with pytest.raises(ValueError, match="accepted_N must be 3"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_predecessor_chain_status_blocked(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       predecessor_chain_status="blocked_predecessor_not_truth")
    with pytest.raises(ValueError, match="predecessor_chain_status is blocked"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_check_dict_helper_works():
    assert check_dict_for_invalid({"a": 1.0}) is True
    assert check_dict_for_invalid({"a": float('inf')}) is False
    assert check_dict_for_invalid([1.0, 2.0]) is True
    assert check_dict_for_invalid([float('nan')]) is False

def test_missing_evidence_path_fails(temp_evidence_dir):
    base_dir, _, _, _, _, _, _, _ = temp_evidence_dir
    # we need a valid hash format for a non-existent file to get to the missing path check
    fake_hash = "a" * 64
    decision = replace(get_valid_decision(), evidence=[Evidence(path="does_not_exist.json", sha256=fake_hash)])
    with pytest.raises(ValueError, match="Evidence path missing: does_not_exist.json"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_hash_mismatch_fails(temp_evidence_dir):
    base_dir, valid_file, _, _, _, _, _, _ = temp_evidence_dir
    wrong_hash = "0" * 64
    decision = replace(get_valid_decision(), evidence=[Evidence(path=valid_file, sha256=wrong_hash)])
    with pytest.raises(ValueError, match="Hash mismatch"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_truth_mutation_requested_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _ , _, _ = temp_evidence_dir
    rc_path = base_dir / "receipt_mut.json"
    with open(rc_path, "w") as f:
        json.dump({"truth_mutation_requested": True}, f)

    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       source_receipt_candidate="receipt_mut.json")
    with pytest.raises(ValueError, match="Source receipt candidate has truth_mutation_requested: true"):
        validate_truth_gate_decision(decision, str(base_dir))

# NEW HARDENING TESTS

def test_path_traversal_evidence_path_rejected(temp_evidence_dir):
    base_dir, _, _, _, _, _, _, _ = temp_evidence_dir
    outside_file = base_dir.parent / "outside.json"
    with open(outside_file, "w") as f: f.write('{}')
    outside_hash = hashlib.sha256(b'{}').hexdigest()

    decision = replace(get_valid_decision(), evidence=[Evidence(path="../outside.json", sha256=outside_hash)])
    with pytest.raises(ValueError, match="Evidence path escapes base_dir"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_malformed_hash_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(), evidence=[Evidence(path=valid_file, sha256="short")])
    with pytest.raises(ValueError, match="Invalid SHA256 format"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_empty_evidence_rejected_for_truth_value(temp_evidence_dir):
    base_dir, _, _, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(), evidence=[])
    with pytest.raises(ValueError, match="requires at least one evidence artifact"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_missing_source_artifact_manifest_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       source_artifact_manifest="missing_manifest.json")
    with pytest.raises(ValueError, match="Required source file missing: missing_manifest.json"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_missing_source_hashes_file_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       source_hashes_file="missing_hashes.sha256")
    with pytest.raises(ValueError, match="Required source file missing: missing_hashes.sha256"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_invalid_literal_like_field_rejected(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       claim_type="unknown_claim")
    with pytest.raises(ValueError, match="Invalid claim_type: unknown_claim"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_parse_constant_rejects_nan_infinity(temp_evidence_dir):
    base_dir, _, _, invalid_file, invalid_hash, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(), evidence=[Evidence(path=invalid_file, sha256=invalid_hash)])
    with pytest.raises(ValueError, match="NaN or Infinity sentinel found at parse time"):
        validate_truth_gate_decision(decision, str(base_dir))

def test_candidate_chain_still_blocked_unless_policy_enabled(temp_evidence_dir):
    base_dir, valid_file, valid_hash, _, _, _, _, _ = temp_evidence_dir
    decision = replace(get_valid_decision(),
                       evidence=[Evidence(path=valid_file, sha256=valid_hash)],
                       predecessor_chain_status="verified_candidate_chain")

    with pytest.raises(ValueError, match="Candidate chain policy not enabled"):
        validate_truth_gate_decision(decision, str(base_dir))

    assert validate_truth_gate_decision(decision, str(base_dir), allow_candidate_chain=True) is True
