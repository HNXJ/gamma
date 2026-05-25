import time
import uuid
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import statistics
from typing import List, Dict, Any, Optional
import dataclasses

@dataclasses.dataclass
class AdmissionRequest:
    run_id: str
    mission_id: str
    requested_turns: int
    target_turns_per_hour: int
    player_profile_id: str
    judge_profile_id: str
    player_harness_id: str
    judge_harness_id: str
    player_model_identity: str
    judge_model_identity: str
    backend_mode: str = "mock"
    auth_mode: str = "none"
    allowed_tools: List[str] = dataclasses.field(default_factory=list)
    artifact_policy: str = "strict"
    transcript_policy: str = "full"
    truth_mode: str = "truth_safe_unverified"
    claim_policy: str = "infrastructure_only"
    stop_conditions: List[str] = dataclasses.field(default_factory=lambda: ["10_turns_reached"])

@dataclasses.dataclass
class MockSessionManifest:
    run_id: str
    session_id: str
    admitted: bool
    admission_status: str
    started_at_utc: str
    ended_at_utc: str
    player_lane: str
    judge_lane: str
    player_harness_id: str
    judge_harness_id: str
    mock_live_boundary: str
    artifact_root: str
    transcript_root: str
    turn_count_requested: int
    turn_count_completed: int
    target_turns_per_hour: float
    measured_turns_per_hour: float
    truth_status: str = "truth_safe_unverified"

@dataclasses.dataclass
class DriftCheck:
    passed: bool
    findings: List[str]

@dataclasses.dataclass
class JudgeVerdict:
    verdict: str
    drift_detected: bool
    truth_safety_passed: bool
    mock_live_boundary_passed: bool
    notes: str

@dataclasses.dataclass
class TurnEnvelope:
    run_id: str
    session_id: str
    turn_id: int
    mission_id: str
    player_id: str
    judge_id: str
    player_harness_id: str
    judge_harness_id: str
    player_model_identity: str
    judge_model_identity: str
    backend_mode: str
    turn_started_at_utc: str
    turn_ended_at_utc: str
    duration_seconds: float
    prompt_or_objective: str
    player_response_summary: str
    judge_verdict: JudgeVerdict
    drift_check: DriftCheck
    transcript_path: str
    artifact_manifest_path: str
    claim_type: str
    truth_status: str = "truth_safe_unverified"
    next_turn_status: str = "continue"
    stop_reason: Optional[str] = None

class MockPlayerHarness:
    def execute_turn(self, turn_id: int) -> str:
        time.sleep(0.01) # Simulate slight overhead
        return f"[MOCK PLAYER] Completed action {turn_id}. No biological result. No simulation result. No Truth-plane mutation."

class MockJudgeHarness:
    def evaluate_turn(self, turn_id: int, response: str) -> JudgeVerdict:
        return JudgeVerdict(
            verdict="pass",
            drift_detected=False,
            truth_safety_passed=True,
            mock_live_boundary_passed=True,
            notes="Mock evaluation. truth_status: truth_safe_unverified."
        )

class MockAdmissionRunner:
    def __init__(self, request: AdmissionRequest, file_prefix: str = ""):
        self.request = request
        self.file_prefix = file_prefix
        self.session_id = f"sess-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        # Use UTC timestamp format YYYYMMDD_HHMMSS
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("outputs/gamma_labyrinth/mock_admission") / ts
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.player = MockPlayerHarness()
        self.judge = MockJudgeHarness()
        self.turn_envelopes: List[TurnEnvelope] = []
        self.durations: List[float] = []

    def run(self):
        run_start = time.time()
        # Write AdmissionRequest
        with open(self.output_dir / f"{self.file_prefix}admission_request.json", "w") as f:
            json.dump(dataclasses.asdict(self.request), f, indent=2)
        turns_completed = 0
        turn_objectives = [
            "inspect mission doctrine summary",
            "propose next bounded action",
            "perform truth-safety self-check",
            "identify required artifact fields",
            "report mock/live boundary",
            "preserve negative-result rule",
            "verify no N=4 unlock",
            "verify blocked model profiles remain blocked",
            "produce next-turn intent",
            "summarize session state"
        ]
        for i in range(self.request.requested_turns):
            turn_start = time.time()
            objective = turn_objectives[i % len(turn_objectives)]
            response = self.player.execute_turn(i)
            verdict = self.judge.evaluate_turn(i, response)
            turn_end = time.time()
            duration = turn_end - turn_start
            self.durations.append(duration)
            transcript_path = self.output_dir / f"{self.file_prefix}transcript_turn_{i}.txt"
            with open(transcript_path, "w") as f:
                f.write(f"Objective: {objective}\n")
                f.write(f"Player: {response}\n")
                f.write(f"Judge: {verdict.verdict}\n")
                f.write(f"Truth Status: truth_safe_unverified\n")
                f.write(f"Claim Type: runtime_infrastructure_evidence\n")
            envelope = TurnEnvelope(
                run_id=self.request.run_id,
                session_id=self.session_id,
                turn_id=i,
                mission_id=self.request.mission_id,
                player_id="G01",
                judge_id="J01",
                player_harness_id=self.request.player_harness_id,
                judge_harness_id=self.request.judge_harness_id,
                player_model_identity=self.request.player_model_identity,
                judge_model_identity=self.request.judge_model_identity,
                backend_mode=self.request.backend_mode,
                turn_started_at_utc=datetime.fromtimestamp(turn_start, tz=timezone.utc).isoformat(),
                turn_ended_at_utc=datetime.fromtimestamp(turn_end, tz=timezone.utc).isoformat(),
                duration_seconds=duration,
                prompt_or_objective=objective,
                player_response_summary=response,
                judge_verdict=verdict,
                drift_check=DriftCheck(passed=True, findings=[]),
                transcript_path=transcript_path.as_posix(),
                artifact_manifest_path=f"{self.file_prefix}artifact_manifest.json",
                claim_type="runtime_infrastructure_evidence",
                truth_status="truth_safe_unverified",
                next_turn_status="continue",
                stop_reason=None
            )
            self.turn_envelopes.append(envelope)
            turns_completed += 1
        run_end = time.time()
        total_duration = run_end - run_start
        measured_tph = (turns_completed / total_duration) * 3600 if total_duration > 0 else float("inf")
        # Session Manifest
        manifest = MockSessionManifest(
            run_id=self.request.run_id,
            session_id=self.session_id,
            admitted=True,
            admission_status="admitted_mock",
            started_at_utc=datetime.fromtimestamp(run_start, tz=timezone.utc).isoformat(),
            ended_at_utc=datetime.fromtimestamp(run_end, tz=timezone.utc).isoformat(),
            player_lane="execution",
            judge_lane="validation",
            player_harness_id=self.request.player_harness_id,
            judge_harness_id=self.request.judge_harness_id,
            mock_live_boundary="pass",
            artifact_root=self.output_dir.as_posix(),
            transcript_root=self.output_dir.as_posix(),
            turn_count_requested=self.request.requested_turns,
            turn_count_completed=turns_completed,
            target_turns_per_hour=self.request.target_turns_per_hour,
            measured_turns_per_hour=measured_tph,
            truth_status="truth_safe_unverified"
        )
        with open(self.output_dir / f"{self.file_prefix}session_manifest.json", "w") as f:
            json.dump(dataclasses.asdict(manifest), f, indent=2)
        # Turn Envelopes JSONL
        with open(self.output_dir / f"{self.file_prefix}turn_envelopes.jsonl", "w") as f:
            for env in self.turn_envelopes:
                f.write(json.dumps(dataclasses.asdict(env)) + "\n")
        # Mock Judge Verdicts JSONL
        with open(self.output_dir / f"{self.file_prefix}mock_judge_verdicts.jsonl", "w") as f:
            for env in self.turn_envelopes:
                f.write(json.dumps(dataclasses.asdict(env.judge_verdict)) + "\n")
        # Cadence Report
        report = {
            "run_id": self.request.run_id,
            "session_id": self.session_id,
            "mode": self.request.backend_mode,
            "target_turns_per_hour": self.request.target_turns_per_hour,
            "turns_attempted": self.request.requested_turns,
            "turns_completed": turns_completed,
            "total_duration_seconds": total_duration,
            "measured_turns_per_hour": measured_tph,
            "median_turn_duration_seconds": statistics.median(self.durations) if self.durations else 0,
            "max_turn_duration_seconds": max(self.durations) if self.durations else 0,
            "pass_fail": "pass" if measured_tph >= self.request.target_turns_per_hour and turns_completed == self.request.requested_turns else "fail",
            "truth_status": "truth_safe_unverified"
        }
        with open(self.output_dir / f"{self.file_prefix}cadence_report.json", "w") as f:
            json.dump(report, f, indent=2)
        # Artifact Manifest
        artifact_manifest = {
            "run_id": self.request.run_id,
            "artifacts": [f.name for f in self.output_dir.iterdir() if f.is_file() and f.name != "hashes.sha256" and f.name.startswith(self.file_prefix)]
        }
        with open(self.output_dir / f"{self.file_prefix}artifact_manifest.json", "w") as f:
            json.dump(artifact_manifest, f, indent=2)
        # Hashes
        hash_lines = []
        for file_path in self.output_dir.iterdir():
            if file_path.is_file() and file_path.name != "hashes.sha256":
                file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                hash_lines.append(f"{file_hash} *{file_path.name}")
        with open(self.output_dir / "hashes.sha256", "w") as f:
            f.write("\n".join(hash_lines) + "\n")
        return report, self.output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gamma Mock Admission Smoke")
    parser.add_argument("--mode", type=str, default="mock", choices=["mock"])
    parser.add_argument("--turns", type=int, default=10)
    parser.add_argument("--target-turns-per-hour", type=int, default=10)
    args = parser.parse_args()
    request = AdmissionRequest(
        run_id=f"run-{int(time.time())}-{uuid.uuid4().hex[:8]}",
        mission_id="runtime_mock_admission_10turns",
        requested_turns=args.turns,
        target_turns_per_hour=args.target_turns_per_hour,
        player_profile_id="gemma4-parallel",
        judge_profile_id="gemma-9b-schiz",
        player_harness_id="harness_mock_player",
        judge_harness_id="harness_mock_judge",
        player_model_identity="gemma-4-e4b-it",
        judge_model_identity="gemma-2-9b-it",
        backend_mode=args.mode
    )
    runner = MockAdmissionRunner(request)
    report, out_dir = runner.run()
    print(f"Mock Admission run complete. Artifacts in: {out_dir}")
    print(json.dumps(report, indent=2))
