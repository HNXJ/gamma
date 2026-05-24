import pytest
import json
import os
from pathlib import Path
from gamma_runtime.turn_cadence import run_cadence_smoke

def test_turn_cadence_contract():
    # Run the smoke benchmark
    manifest, out_dir = run_cadence_smoke(mode="dry_run", target_turns=10, target_tph=10)

    # 1. 10 turns completed
    assert manifest["turns_completed"] == 10
    
    # 2. measured_turns_per_hour >= 10
    assert manifest["measured_turns_per_hour"] >= 10

    # 3. Verify manifest persistence
    manifest_path = out_dir / "cadence_manifest.json"
    assert manifest_path.exists()
    assert manifest["manifest_persistence"] == "pass"

    # 4. Verify mock/live boundary
    assert manifest["mock_live_boundary"] == "pass"
    assert manifest["mode"] == "dry_run"
    assert manifest["truth_status"] == "truth_safe_unverified"

    # 5. Load turn records and verify contract
    turn_records_path = out_dir / "turn_records.jsonl"
    assert turn_records_path.exists()

    records = []
    with open(turn_records_path, "r") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    assert len(records) == 10

    for record in records:
        # Check identity
        assert "session_id" in record
        assert "player_id" in record
        assert "harness_id" in record
        assert record["backend_mode"] == "dry_run"
        
        # Check truth discipline
        assert record["truth_status"] == "truth_safe_unverified"
        assert record["claim_type"] == "runtime_infrastructure_evidence"
        
        # Transcript stub exists
        assert record["transcript_path"] is not None
        assert Path(record["transcript_path"]).exists()

        # No biological/scientific claims
        claim_str = json.dumps(record).lower()
        forbidden = [
            "biological", "omission", "e/i", 
            "n=3 closure", "n=4", "accepted truth", "truth-plane promotion"
        ]
        for f in forbidden:
            assert f not in claim_str, f"Forbidden term '{f}' found in turn record."

