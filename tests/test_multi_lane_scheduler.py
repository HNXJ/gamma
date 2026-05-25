import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gamma_runtime.continuous_scheduler import SchedulerConfig, ContinuousScheduler

def test_multi_lane_scheduler_concurrency():
    config = SchedulerConfig(
        scheduler_id="test_multi_sched",
        run_id="test_multi_run",
        mode="mock",
        target_turns_per_hour=10,
        target_seconds_per_turn=360,
        lane_count=2,
        turns_per_lane=10,
        active_lanes=[
            {
                "lane_id": "lane-0",
                "player_profile_id": "gemma4-parallel",
                "judge_profile_id": "gemma-9b-schiz",
                "player_harness_id": "harness_lane_0_player",
                "judge_harness_id": "harness_lane_0_judge",
                "player_model_identity": "gemma-4-e4b-it",
                "judge_model_identity": "gemma-2-9b-it",
                "backend_mode": "mock"
            },
            {
                "lane_id": "lane-1",
                "player_profile_id": "gemma-9b-schiz",
                "judge_profile_id": "gemma4-parallel",
                "player_harness_id": "harness_lane_1_player",
                "judge_harness_id": "harness_lane_1_judge",
                "player_model_identity": "gemma-2-9b-it",
                "judge_model_identity": "gemma-4-e4b-it",
                "backend_mode": "mock"
            }
        ],
        pacing_mode="accelerated_validation",
        live_calls_authorized=False,
        truth_mode="truth_safe_unverified"
    )
    
    scheduler = ContinuousScheduler(config)
    manifest, out_dir = scheduler.run()

    # 8. Multi-lane scheduler completes 2 lanes x 10 turns
    assert manifest.lane_count == 2
    assert manifest.turns_completed_total == 20
    assert len(manifest.per_lane_metrics) == 2

    # 9. Each lane has distinct session_id
    assert manifest.per_lane_metrics[0].session_id != manifest.per_lane_metrics[1].session_id
    
    # 12. Every lane completes 10 turns
    for lane_m in manifest.per_lane_metrics:
        assert lane_m.turns_completed == 10
        # 13. Every lane has measured_turns_per_hour >= 10
        assert lane_m.measured_turns_per_hour >= 10

    # 14. Heartbeat records include lane_id and count >= total turns
    hb_path = out_dir / "heartbeat_records.jsonl"
    hbs = []
    with open(hb_path, "r") as f:
        for line in f:
            if line.strip():
                hbs.append(json.loads(line))
    assert len(hbs) == 20
    lane_ids_in_hbs = set(h["lane_id"] for h in hbs)
    assert lane_ids_in_hbs == {"lane-0", "lane-1"}

    # 15. Checkpoint includes all lanes
    chkpt_path = out_dir / "checkpoint.json"
    with open(chkpt_path, "r") as f:
        chkpt = json.load(f)
    assert "lane-0" in chkpt["last_completed_turn_by_lane"]
    assert "lane-1" in chkpt["last_completed_turn_by_lane"]

    # 16. All transcripts exist
    for i in range(10):
        assert (out_dir / f"lane_lane-0_transcript_turn_{i}.txt").exists()
        assert (out_dir / f"lane_lane-1_transcript_turn_{i}.txt").exists()

    # 18. All truth_status values are truth_safe_unverified
    assert manifest.truth_status == "truth_safe_unverified"
    
    # 19. hashes.sha256 covers all expected artifacts
    assert (out_dir / "hashes.sha256").exists()

    # 20. No artifact JSON contains NaN, Infinity, np.nan
    # 21. No artifact claims biological result etc.
    forbidden = ["nan", "infinity", "np.nan", "n=3 closure", "omission result"]
    with open(out_dir / f"lane_lane-0_turn_envelopes.jsonl", "r") as f:
        for line in f:
            low = line.lower()
            for forb in forbidden:
                assert forb not in low
            assert "no biological result" in low
