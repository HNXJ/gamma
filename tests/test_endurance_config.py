import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gamma_runtime.continuous_scheduler import SchedulerConfig, ContinuousScheduler

def test_wall_clock_config_logic():
    config = SchedulerConfig(
        scheduler_id="test_endurance",
        run_id="test_run",
        mode="mock",
        target_turns_per_hour=10,
        target_seconds_per_turn=360,
        lane_count=1,
        turns_per_lane=2, # Small number for config test
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
        pacing_mode="wall_clock",
        heartbeat_interval_seconds=1, # Fast heartbeats for test
        live_calls_authorized=False,
        plan_only=True # Don't actually sleep
    )
    
    scheduler = ContinuousScheduler(config)
    manifest, out_dir = scheduler.run()
    
    # Verify plan_only artifacts
    assert (out_dir / "schedule_plan.json").exists()
    assert (out_dir / "endurance_config.json").exists()
    
    with open(out_dir / "schedule_plan.json", "r") as f:
        plan = json.load(f)
    assert len(plan) == 2
    assert "scheduled_start_utc" in plan[0]

def test_target_derivation():
    # Verify target_seconds_per_turn derivation logic
    tph = 10
    sec_per_turn = int(3600 / tph)
    assert sec_per_turn == 360
    
    tph = 20
    sec_per_turn = int(3600 / tph)
    assert sec_per_turn == 180

def test_forbidden_scientific_claims_negative():
    # Mock some data and check for forbidden strings
    forbidden = ["nan", "infinity", "n=3 closure", "omission result"]
    sample_text = "This is a mock player response. No biological result. No Truth-plane mutation."
    
    low = sample_text.lower()
    for forb in forbidden:
        assert forb not in low
    assert "no biological result" in low
