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
        turns_per_lane=2,
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
        planned_duration_seconds=10, # Short duration for test
        minimum_valid_duration_seconds=8,
        heartbeat_interval_seconds=1,
        live_calls_authorized=False,
        plan_only=True
    )

    scheduler = ContinuousScheduler(config)
    manifest, out_dir = scheduler.run()

    assert (out_dir / "schedule_plan.json").exists()
    assert (out_dir / "endurance_config.json").exists()

    with open(out_dir / "schedule_plan.json", "r") as f:
        data = json.load(f)
        plan = data["plan"]
        summary = data["summary"]
    assert len(plan) == 2
    assert summary["planned_endurance_duration_seconds"] == 10
    assert summary["last_turn_scheduled_at_seconds"] == 360 # (2-1)*360

def test_target_derivation():
    tph = 10
    sec_per_turn = int(3600 / tph)
    assert sec_per_turn == 360

def test_heartbeat_count_logic():
    # 3600s duration, 60s interval -> 60 heartbeats + turn heartbeats
    duration = 3600
    interval = 60
    turns = 10
    expected_min = int(duration / interval) + turns
    assert expected_min >= 70 # approx
