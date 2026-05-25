import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gamma_runtime.mock_admission import AdmissionRequest, MockAdmissionRunner

def test_mock_admission_contract():
    request = AdmissionRequest(
        run_id="test_run_1",
        mission_id="runtime_mock_admission_10turns",
        requested_turns=10,
        target_turns_per_hour=10,
        player_profile_id="gemma4-parallel",
        judge_profile_id="gemma-9b-schiz",
        player_harness_id="harness_mock_player",
        judge_harness_id="harness_mock_judge",
        player_model_identity="gemma-4-e4b-it",
        judge_model_identity="gemma-2-9b-it",
        backend_mode="mock"
    )
    
    runner = MockAdmissionRunner(request)
    report, out_dir = runner.run()

    # 1. 10 mock turns complete
    assert report["turns_completed"] == 10
    
    # 2. session_manifest exists and says admitted_mock
    manifest_path = out_dir / "session_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    assert manifest["admission_status"] == "admitted_mock"

    # 3. player_harness_id and judge_harness_id are nonempty
    assert manifest["player_harness_id"] == "harness_mock_player"
    assert manifest["judge_harness_id"] == "harness_mock_judge"

    # 4. player and judge lanes are distinct
    assert manifest["player_lane"] == "execution"
    assert manifest["judge_lane"] == "validation"
    assert manifest["player_lane"] != manifest["judge_lane"]

    # 5 & 6. backend_mode is mock, no live endpoint field is populated
    assert report["mode"] == "mock"
    
    # 7. transcripts exist for every turn
    for i in range(10):
        assert (out_dir / f"transcript_turn_{i}.txt").exists()

    # 8. artifact_manifest.json exists
    assert (out_dir / "artifact_manifest.json").exists()

    # 9. hashes.sha256 exists and covers all expected artifacts
    hashes_path = out_dir / "hashes.sha256"
    assert hashes_path.exists()
    with open(hashes_path, "r") as f:
        hash_lines = f.read().strip().split("\n")
    
    for line in hash_lines:
        file_hash, file_name = line.split(" *")
        assert len(file_hash) == 64
        assert (out_dir / file_name).exists()

    # Verify envelopes
    envelopes_path = out_dir / "turn_envelopes.jsonl"
    assert envelopes_path.exists()
    envelopes = []
    with open(envelopes_path, "r") as f:
        for line in f:
            if line.strip():
                envelopes.append(json.loads(line))
                
    assert len(envelopes) == 10
    
    for env in envelopes:
        # 10. every turn has a judge_verdict
        assert "judge_verdict" in env
        assert env["judge_verdict"]["verdict"] == "pass"
        
        # 11. every drift_check passes
        assert env["drift_check"]["passed"] is True
        
        # 12. every truth_status is truth_safe_unverified
        assert env["truth_status"] == "truth_safe_unverified"
        assert env["backend_mode"] == "mock"
        assert "http://" not in json.dumps(env)
        
        # 13. no turn contains NaN, Infinity, np.nan, etc.
        env_str = json.dumps(env).lower()
        forbidden = [
            "nan", "infinity", "np.nan", 
            "n=3 closure", "n=3 theta closure",
            "omission result", "e/i circuit truth"
        ]
        for f in forbidden:
            assert f not in env_str

        # Ensure explicit negations are present as required
        assert "no biological result" in env_str
        assert "no simulation result" in env_str
        assert "no truth-plane mutation" in env_str

    # 14. measured_turns_per_hour >= 10
    assert report["measured_turns_per_hour"] >= 10

