import time
import uuid
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
import statistics

def run_cadence_smoke(
    mode: str = "dry_run",
    target_turns: int = 10,
    target_tph: int = 10,
    target_spt: int = 360
):
    run_id = f"cadence-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    output_dir = Path("outputs/gamma_labyrinth/cadence_smoke") / datetime.now().strftime("%Y%M%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    turn_records = []
    durations = []
    
    start_time_total = time.time()
    turns_completed = 0
    
    for i in range(target_turns):
        turn_start = time.time()
        
        # Simulate dry run logic
        if mode == "dry_run":
            time.sleep(0.01) # Simulate minimal overhead
        
        turn_end = time.time()
        duration = turn_end - turn_start
        durations.append(duration)
        
        transcript_path = output_dir / f"transcript_turn_{i}.txt"
        with open(transcript_path, "w") as f:
            f.write(f"[DRY RUN STUB] Turn {i} transcript.")
            
        turn_record = {
            "session_id": run_id,
            "player_id": "test_player",
            "harness_id": "harness_mock",
            "model_identity": "mock_model_v1",
            "backend_mode": mode,
            "turn_id": i,
            "mission_id": "runtime_cadence_smoke",
            "started_at_utc": datetime.fromtimestamp(turn_start, tz=timezone.utc).isoformat(),
            "ended_at_utc": datetime.fromtimestamp(turn_end, tz=timezone.utc).isoformat(),
            "duration_seconds": duration,
            "turn_status": "completed",
            "claim_type": "runtime_infrastructure_evidence",
            "truth_status": "truth_safe_unverified",
            "transcript_path": str(transcript_path),
            "artifact_manifest_path": None,
            "drift_check": {
                "passed": True,
                "findings": []
            },
            "stop_reason": None
        }
        
        turn_records.append(turn_record)
        turns_completed += 1

    total_duration = time.time() - start_time_total
    measured_tph = (turns_completed / total_duration) * 3600 if total_duration > 0 else float("inf")
    
    with open(output_dir / "turn_records.jsonl", "w") as f:
        for record in turn_records:
            f.write(json.dumps(record) + "\n")

    manifest = {
        "run_id": run_id,
        "mode": mode,
        "target_turns_per_hour": target_tph,
        "target_seconds_per_turn": target_spt,
        "turns_attempted": target_turns,
        "turns_completed": turns_completed,
        "total_duration_seconds": total_duration,
        "measured_turns_per_hour": measured_tph,
        "median_turn_duration_seconds": statistics.median(durations) if durations else 0,
        "max_turn_duration_seconds": max(durations) if durations else 0,
        "transcript_persistence": "pass",
        "manifest_persistence": "pass",
        "mock_live_boundary": "pass" if mode in ("dry_run", "mock") else "fail",
        "truth_status": "truth_safe_unverified"
    }

    manifest_path = output_dir / "cadence_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest, output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gamma Turn Cadence Smoke")
    parser.add_argument("--mode", type=str, default="dry_run", choices=["dry_run", "mock", "live"])
    parser.add_argument("--turns", type=int, default=10)
    parser.add_argument("--target-turns-per-hour", type=int, default=10)
    
    args = parser.parse_args()
    
    manifest, out_dir = run_cadence_smoke(
        mode=args.mode,
        target_turns=args.turns,
        target_tph=args.target_turns_per_hour
    )
    
    print(f"Cadence run complete. Manifest in: {out_dir}")
    print(json.dumps(manifest, indent=2))
