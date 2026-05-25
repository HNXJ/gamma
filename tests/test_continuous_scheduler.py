import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gamma_runtime.continuous_scheduler import SchedulerConfig, ContinuousScheduler

def test_continuous_scheduler_contract():
    config = SchedulerConfig(
        scheduler_id="test_sched_1",
        run_id="test_run_1",
        mode="mock",
        target_turns_per_hour=10,
        target_seconds_per_turn=360,
        lane_count=1,
        turns_per_lane=10,
        active_lanes=[{
            "lane_id": "lane-1",
            "player_profile_id": "gemma4-parallel",
            "judge_profile_id": "gemma-9b-schiz",
            "player_harness_id": "harness_mock_player",
            "judge_harness_id": "harness_mock_judge",
            "player_model_identity": "gemma-4-e4b-it",
            "judge_model_identity": "gemma-2-9b-it",
            "backend_mode": "mock"
        }],
        pacing_mode="accelerated_validation",
        live_calls_authorized=False,
        truth_mode="truth_safe_unverified"
    )
    
    scheduler = ContinuousScheduler(config)
    manifest, out_dir = scheduler.run()

    # 1. Scheduler completes 10 mock-admitted turns
    assert manifest.turns_completed_total == 10

    # 2. Scheduler config has target_turns_per_hour == 10
    config_path = out_dir / "scheduler_config.json"
    assert config_path.exists()
    with open(config_path, "r") as f:
        conf = json.load(f)
    assert conf["target_turns_per_hour"] == 10

    # 6. backend_mode == mock
    assert manifest.mode == "mock"

    # 7. player/judge lanes remain separated
    sm_path = out_dir / "lane_lane-1_session_manifest.json"
    with open(sm_path, "r") as f:
        sm = json.load(f)
    assert sm["player_lane"] == "execution"
    assert sm["judge_lane"] == "validation"

    # 8. heartbeat records exist
    hb_path = out_dir / "heartbeat_records.jsonl"
    assert hb_path.exists()

    # 9. checkpoint exists
    chkpt_path = out_dir / "final_checkpoint.json"
    assert chkpt_path.exists()

    # 10. checkpoint records last_completed_turn == 9
    with open(chkpt_path, "r") as f:
        chkpt = json.load(f)
    assert chkpt["last_completed_turn_by_lane"]["lane-1"] == 9

    # 12. all turn envelopes exist
    assert (out_dir / "lane_lane-1_turn_envelopes.jsonl").exists()

    # 16. hashes.sha256 covers all artifacts
    hashes_path = out_dir / "hashes.sha256"
    assert hashes_path.exists()
    
    # 18. all truth_status fields are truth_safe_unverified
    assert manifest.truth_status == "truth_safe_unverified"

    # 20. no blocked model profile is routed
    audit_path = out_dir / "live_route_readiness.json"
    assert audit_path.exists()
    with open(audit_path, "r") as f:
        audit = json.load(f)
    for p in audit["live_route_readiness"]["mock_safe_profiles_from_registry"]:
        assert "blocked" not in p.get("readiness_status", "")

    # 22. no artifact JSON contains NaN
    forbidden = ["nan", "infinity", "np.nan"]
    with open(out_dir / "lane_lane-1_turn_envelopes.jsonl", "r") as f:
        for line in f:
            low = line.lower()
            for forb in forbidden:
                assert forb not in low
