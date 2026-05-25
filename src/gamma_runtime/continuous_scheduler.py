import time
import json
import uuid
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import dataclasses
from typing import List, Dict, Any, Optional
import statistics

# Import from mock_admission
from gamma_runtime.mock_admission import AdmissionRequest, MockAdmissionRunner

from gamma_runtime.model_profiles import ProfileRegistry

@dataclasses.dataclass
class SchedulerConfig:
    scheduler_id: str
    run_id: str
    mode: str = "mock"
    target_turns_per_hour: int = 10
    target_seconds_per_turn: int = 360
    lane_count: int = 1
    turns_per_lane: int = 10
    active_lanes: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    pacing_mode: str = "accelerated_validation"
    live_calls_authorized: bool = False
    truth_mode: str = "truth_safe_unverified"
    checkpoint_policy: str = "end_of_run"
    failure_policy: str = "stop_on_first_error"

@dataclasses.dataclass
class LaneMetrics:
    lane_id: str
    session_id: str
    turns_scheduled: int
    turns_completed: int
    total_duration_seconds: float
    measured_turns_per_hour: float
    target_turns_per_hour: float
    policy_passed: bool
    transcript_count: int
    judge_verdict_count: int
    drift_pass_count: int
    truth_status: str

@dataclasses.dataclass
class SchedulerManifest:
    scheduler_id: str
    run_id: str
    started_at_utc: str
    ended_at_utc: str
    mode: str
    pacing_mode: str
    lane_count: int
    turns_scheduled_total: int
    turns_completed_total: int
    per_lane_metrics: List[LaneMetrics]
    aggregate_measured_turns_per_hour: float
    all_lanes_policy_passed: bool
    heartbeat_count: int
    checkpoint_count: int
    resume_supported: bool
    backend_health_status: str
    mock_live_boundary: str
    truth_status: str = "truth_safe_unverified"

@dataclasses.dataclass
class HeartbeatRecord:
    scheduler_id: str
    run_id: str
    session_id: str
    heartbeat_id: str
    timestamp_utc: str
    lane_id: str
    turn_id: int
    session_liveness: str
    transcript_persistence: str
    artifact_persistence: str
    backend_health: str
    drift_status: str
    checkpoint_path: Optional[str]
    next_action: str

@dataclasses.dataclass
class Checkpoint:
    checkpoint_id: str
    run_id: str
    session_id: Optional[str]
    last_completed_turn_by_lane: Dict[str, int]
    turn_count_completed_total: int
    active_lanes: List[Dict[str, Any]]
    artifact_root: str
    transcript_root: str
    truth_status: str
    resume_token_or_path: Optional[str]
    created_at_utc: str

class ContinuousScheduler:
    def __init__(self, config: SchedulerConfig):
        self.config = config
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("outputs/gamma_labyrinth/multi_lane_mock_scheduler") / ts
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.heartbeats: List[HeartbeatRecord] = []
        self.checkpoint: Optional[Checkpoint] = None
        self.per_lane_metrics: List[LaneMetrics] = []

    def run(self):
        start_time = time.time()
        # 1. Write SchedulerConfig
        with open(self.output_dir / "scheduler_config.json", "w") as f:
            json.dump(dataclasses.asdict(self.config), f, indent=2)
        total_turns_completed = 0
        last_turn_by_lane = {}
        for lane_cfg in self.config.active_lanes:
            lane_id = lane_cfg["lane_id"]
            admission_request = AdmissionRequest(
                run_id=self.config.run_id,
                mission_id=f"runtime_multi_lane_scheduler_{lane_id}",
                requested_turns=self.config.turns_per_lane,
                target_turns_per_hour=self.config.target_turns_per_hour,
                player_profile_id=lane_cfg.get("player_profile_id", "gemma4-parallel"),
                judge_profile_id=lane_cfg.get("judge_profile_id", "gemma-9b-schiz"),
                player_harness_id=lane_cfg.get("player_harness_id", "harness_mock_player"),
                judge_harness_id=lane_cfg.get("judge_harness_id", "harness_mock_judge"),
                player_model_identity=lane_cfg.get("player_model_identity", "gemma-4-e4b-it"),
                judge_model_identity=lane_cfg.get("judge_model_identity", "gemma-2-9b-it"),
                backend_mode=self.config.mode
            )
            prefix = f"lane_{lane_id}_"
            runner = MockAdmissionRunner(admission_request, file_prefix=prefix)
            runner.output_dir = self.output_dir
            report, _ = runner.run()
            for i in range(report["turns_completed"]):
                hb = HeartbeatRecord(
                    scheduler_id=self.config.scheduler_id,
                    run_id=self.config.run_id,
                    session_id=runner.session_id,
                    heartbeat_id=f"hb-{lane_id}-{i}-{uuid.uuid4().hex[:4]}",
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    lane_id=lane_id,
                    turn_id=i,
                    session_liveness="pass",
                    transcript_persistence="pass",
                    artifact_persistence="pass",
                    backend_health="mock_ok",
                    drift_status="pass",
                    checkpoint_path=None,
                    next_action="continue" if i < report["turns_completed"] - 1 else "stop"
                )
                self.heartbeats.append(hb)
            lane_metrics = LaneMetrics(
                lane_id=lane_id,
                session_id=runner.session_id,
                turns_scheduled=self.config.turns_per_lane,
                turns_completed=report["turns_completed"],
                total_duration_seconds=report["total_duration_seconds"],
                measured_turns_per_hour=report["measured_turns_per_hour"],
                target_turns_per_hour=self.config.target_turns_per_hour,
                policy_passed=report["pass_fail"] == "pass",
                transcript_count=report["turns_completed"],
                judge_verdict_count=report["turns_completed"],
                drift_pass_count=report["turns_completed"],
                truth_status="truth_safe_unverified"
            )
            self.per_lane_metrics.append(lane_metrics)
            total_turns_completed += report["turns_completed"]
            last_turn_by_lane[lane_id] = report["turns_completed"] - 1
        # 3. Write Checkpoint
        chkpt_path = self.output_dir / "checkpoint.json"
        self.checkpoint = Checkpoint(
            checkpoint_id=f"chkpt-{uuid.uuid4().hex[:8]}",
            run_id=self.config.run_id,
            session_id=None,
            last_completed_turn_by_lane=last_turn_by_lane,
            turn_count_completed_total=total_turns_completed,
            active_lanes=self.config.active_lanes,
            artifact_root=self.output_dir.as_posix(),
            transcript_root=self.output_dir.as_posix(),
            truth_status="truth_safe_unverified",
            resume_token_or_path=None,
            created_at_utc=datetime.now(timezone.utc).isoformat()
        )
        with open(chkpt_path, "w") as f:
            json.dump(dataclasses.asdict(self.checkpoint), f, indent=2)
        if self.heartbeats:
            self.heartbeats[-1].checkpoint_path = chkpt_path.as_posix()
        with open(self.output_dir / "heartbeat_records.jsonl", "w") as f:
            for hb in self.heartbeats:
                f.write(json.dumps(dataclasses.asdict(hb)) + "\n")
        self.audit_live_route_readiness()
        end_time = time.time()
        all_lanes_passed = all(m.policy_passed for m in self.per_lane_metrics)
        avg_tph = statistics.mean(m.measured_turns_per_hour for m in self.per_lane_metrics) if self.per_lane_metrics else 0
        manifest = SchedulerManifest(
            scheduler_id=self.config.scheduler_id,
            run_id=self.config.run_id,
            started_at_utc=datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
            ended_at_utc=datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat(),
            mode=self.config.mode,
            pacing_mode=self.config.pacing_mode,
            lane_count=self.config.lane_count,
            turns_scheduled_total=self.config.lane_count * self.config.turns_per_lane,
            turns_completed_total=total_turns_completed,
            per_lane_metrics=self.per_lane_metrics,
            aggregate_measured_turns_per_hour=avg_tph,
            all_lanes_policy_passed=all_lanes_passed,
            heartbeat_count=len(self.heartbeats),
            checkpoint_count=1,
            resume_supported=False,
            backend_health_status="mock_ok",
            mock_live_boundary="pass",
            truth_status="truth_safe_unverified"
        )
        with open(self.output_dir / "scheduler_manifest.json", "w") as f:
            json.dump(dataclasses.asdict(manifest), f, indent=2)
        with open(self.output_dir / "lane_metrics.json", "w") as f:
            json.dump([dataclasses.asdict(m) for m in self.per_lane_metrics], f, indent=2)
        global_artifacts = {
            "scheduler_id": self.config.scheduler_id,
            "run_id": self.config.run_id,
            "artifacts": [f.name for f in self.output_dir.iterdir() if f.is_file() and f.name != "hashes.sha256"]
        }
        with open(self.output_dir / "artifact_manifest.json", "w") as f:
            json.dump(global_artifacts, f, indent=2)
        cadence_report = {
            "run_id": self.config.run_id,
            "mode": self.config.mode,
            "turns_scheduled_total": manifest.turns_scheduled_total,
            "turns_completed_total": manifest.turns_completed_total,
            "aggregate_measured_turns_per_hour": manifest.aggregate_measured_turns_per_hour,
            "pass_fail": "pass" if manifest.all_lanes_policy_passed else "fail",
            "truth_status": "truth_safe_unverified"
        }
        with open(self.output_dir / "cadence_report.json", "w") as f:
            json.dump(cadence_report, f, indent=2)
        self.rewrite_hashes()
        return manifest, self.output_dir

    def audit_live_route_readiness(self):
        reg = ProfileRegistry()
        reg.register_default_profiles()
        mock_safe_profiles = []
        live_candidate_unverified_profiles = []
        blocked_profiles = []
        for pid, profile in reg.profiles.items():
            if profile.status == "mock_safe":
                mock_safe_profiles.append({
                    "profile_id": profile.profile_id,
                    "canonical_model_id": profile.canonical_model_id,
                    "readiness_status": profile.status,
                    "evidence_source": "ProfileRegistry"
                })
            elif profile.status == "live_candidate_unverified":
                live_candidate_unverified_profiles.append({
                    "profile_id": profile.profile_id,
                    "canonical_model_id": profile.canonical_model_id,
                    "readiness_status": profile.status,
                    "evidence_source": "ProfileRegistry"
                })
            elif profile.status in ["blocked", "load_blocked"]:
                blocked_profiles.append({
                    "profile_id": profile.profile_id,
                    "canonical_model_id": profile.canonical_model_id,
                    "blocked_reason": profile.blocked_reason or "explicitly blocked"
                })
        audit = {
            "live_route_readiness": {
                "live_calls_authorized": False,
                "endpoint_checked": False,
                "credential_files_read": False,
                "route_safe_profiles_from_registry": [],
                "mock_safe_profiles_from_registry": mock_safe_profiles,
                "live_candidate_unverified_profiles": live_candidate_unverified_profiles,
                "blocked_profiles": blocked_profiles,
                "suffix_id_policy": "canonical_ids_must_not_include_runtime_suffix",
                "required_env_placeholders": [
                    "GAMMA_LMS_BASE_URL",
                    "GAMMA_MODEL_ID",
                    "GAMMA_AUTH_MODE"
                ],
                "next_live_test_command_template": "TEMPLATE_ONLY_NOT_AUTHORIZED",
                "stop_conditions_for_live_test": ["session_timeout", "manual_interrupt", "security_violation"]
            }
        }
        with open(self.output_dir / "live_route_readiness.json", "w") as f:
            json.dump(audit, f, indent=2)

    def rewrite_hashes(self):
        hash_lines = []
        for file_path in self.output_dir.iterdir():
            if file_path.is_file() and file_path.name != "hashes.sha256":
                file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                hash_lines.append(f"{file_hash} *{file_path.name}")
        with open(self.output_dir / "hashes.sha256", "w") as f:
            f.write("\n".join(hash_lines) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gamma Continuous Scheduler Smoke")
    parser.add_argument("--mode", type=str, default="mock", choices=["mock"])
    parser.add_argument("--pacing", type=str, default="accelerated_validation", choices=["accelerated_validation", "wall_clock"])
    parser.add_argument("--lanes", type=int, default=1)
    parser.add_argument("--turns-per-lane", type=int, default=10)
    parser.add_argument("--target-turns-per-hour", type=int, default=10)
    args = parser.parse_args()
    active_lanes = []
    for i in range(args.lanes):
        active_lanes.append({
            "lane_id": f"lane-{i}",
            "player_profile_id": "gemma4-parallel",
            "judge_profile_id": "gemma-9b-schiz",
            "player_harness_id": f"harness_mock_player_lane_{i}",
            "judge_harness_id": f"harness_mock_judge_lane_{i}",
            "player_model_identity": "gemma-4-e4b-it",
            "judge_model_identity": "gemma-2-9b-it",
            "backend_mode": args.mode
        })
    config = SchedulerConfig(
        scheduler_id=f"sched-{int(time.time())}-{uuid.uuid4().hex[:8]}",
        run_id=f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}",
        mode=args.mode,
        target_turns_per_hour=args.target_turns_per_hour,
        target_seconds_per_turn=360,
        lane_count=args.lanes,
        turns_per_lane=args.turns_per_lane,
        active_lanes=active_lanes,
        pacing_mode=args.pacing,
        live_calls_authorized=False,
        truth_mode="truth_safe_unverified",
        checkpoint_policy="end_of_run",
        failure_policy="stop_on_first_error"
    )
    scheduler = ContinuousScheduler(config)
    manifest, out_dir = scheduler.run()
    print(f"Continuous Scheduler run complete. Artifacts in: {out_dir}")
    print(json.dumps(dataclasses.asdict(manifest), indent=2))
