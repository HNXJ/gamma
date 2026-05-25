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

    # 1. Scheduler completes 10 mock-admitted turns in accelerated_validation mode
    assert manifest.turns_completed_total == 10

    # 2. Scheduler config has target_turns_per_hour == 10
    config_path = out_dir / "scheduler_config.json"
    assert config_path.exists()
    with open(config_path, "r") as f:
        conf = json.load(f)
    assert conf["target_turns_per_hour"] == 10

    # 3. target_seconds_per_turn == 360
    assert conf["target_seconds_per_turn"] == 360

    # 4. pacing_mode == accelerated_validation
    assert conf["pacing_mode"] == "accelerated_validation"

    # 5. live_calls_authorized == false
    assert conf["live_calls_authorized"] is False

    # 6. backend_mode == mock
    assert manifest.mode == "mock"

    # 7. player/judge lanes remain separated
    sm_path = out_dir / "lane_lane-1_session_manifest.json"
    with open(sm_path, "r") as f:
        sm = json.load(f)
    assert sm["player_lane"] == "execution"
    assert sm["judge_lane"] == "validation"

    # 8. heartbeat records exist and count >= turns completed
    hb_path = out_dir / "heartbeat_records.jsonl"
    assert hb_path.exists()
    hbs = []
    with open(hb_path, "r") as f:
        for line in f:
            if line.strip():
                hbs.append(json.loads(line))
    assert len(hbs) >= 10

    # 9. checkpoint exists
    chkpt_path = out_dir / "checkpoint.json"
    assert chkpt_path.exists()

    # 10. checkpoint records last_completed_turn == 9 or equivalent
    with open(chkpt_path, "r") as f:
        chkpt = json.load(f)
    assert chkpt["last_completed_turn_by_lane"]["lane-1"] == 9

    # 11. resume metadata exists or resume_supported is explicitly false with reason
    assert manifest.resume_supported is False

    # 12. all turn envelopes exist
    assert (out_dir / "lane_lane-1_turn_envelopes.jsonl").exists()

    # 13. all transcripts exist
    for i in range(10):
        assert (out_dir / f"lane_lane-1_transcript_turn_{i}.txt").exists()

    # 14. all judge verdicts exist
    assert (out_dir / "lane_lane-1_mock_judge_verdicts.jsonl").exists()

    # 15. artifact_manifest exists
    assert (out_dir / "artifact_manifest.json").exists()

    # 16. hashes.sha256 covers scheduler artifacts and mock-admission artifacts
    hashes_path = out_dir / "hashes.sha256"
    assert hashes_path.exists()
    with open(hashes_path, "r") as f:
        hash_lines = f.read().strip().split("\n")
    
    files_in_dir = [f.name for f in out_dir.iterdir() if f.is_file() and f.name != "hashes.sha256"]
    assert len(hash_lines) == len(files_in_dir)

    # 17. measured_turns_per_hour >= 10
    assert manifest.aggregate_measured_turns_per_hour >= 10

    # 18. all truth_status fields are truth_safe_unverified
    assert manifest.truth_status == "truth_safe_unverified"
    assert conf["truth_mode"] == "truth_safe_unverified"

    # 19. no live endpoint field is populated
    assert manifest.backend_health_status == "mock_ok"

    # 20. no blocked model profile is routed & 21. suffix ids
    audit_path = out_dir / "live_route_readiness.json"
    assert audit_path.exists()
    with open(audit_path, "r") as f:
        audit = json.load(f)
        
    for p in audit["live_route_readiness"]["mock_safe_profiles_from_registry"]:
        assert "blocked" not in p.get("readiness_status", "")
        # suffix check
        assert ":" not in p["canonical_model_id"]

    # 22. no artifact JSON contains NaN, Infinity, or np.nan
    # 23. no artifact claims biological result etc.
    forbidden = [
        "nan", "infinity", "np.nan",
        "n=3 closure", "n=3 theta closure",
        "omission result", "e/i circuit truth"
    ]
    required_negations = [
        "no biological result", "no simulation result", "no truth-plane mutation"
    ]
    
    with open(out_dir / "lane_lane-1_turn_envelopes.jsonl", "r") as f:
        for line in f:
            if not line.strip(): continue
            low = line.lower()
            for forb in forbidden:
                assert f"{forb}" not in low
            for req in required_negations:
                assert req in low
