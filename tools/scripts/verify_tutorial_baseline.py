import os
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACT_ROOT = os.path.join(ROOT, "data/tutorials/artifacts/T00_single_neuron_hh")

def verify_latest_t00():
    print(f"Checking T00 baseline in {ARTIFACT_ROOT}...")
    if not os.path.exists(ARTIFACT_ROOT):
        print("FAIL: T00 artifact root missing.")
        return False
        
    runs = [d for d in os.listdir(ARTIFACT_ROOT) if os.path.isdir(os.path.join(ARTIFACT_ROOT, d))]
    if not runs:
        print("FAIL: No T00 runs found.")
        return False
        
    # Get most recent run
    latest_run = max(runs, key=lambda d: os.path.getmtime(os.path.join(ARTIFACT_ROOT, d)))
    run_path = os.path.join(ARTIFACT_ROOT, latest_run)
    print(f"Verifying latest run: {latest_run}")
    
    required_files = [
        "summary_metrics.json",
        "evaluation_decision.json",
        "run_manifest.json",
        "mission_config.json",
        "v_trace.npy"
    ]
    
    for f in required_files:
        if not os.path.exists(os.path.join(run_path, f)):
            print(f"FAIL: Missing required file {f}")
            return False
            
    with open(os.path.join(run_path, "summary_metrics.json"), "r") as f:
        metrics = json.load(f)
        
    if metrics.get("tutorial_id") != "T00_single_neuron_hh":
        print("FAIL: tutorial_id mismatch in metrics.")
        return False
        
    if metrics.get("promotion_eligible") is not False:
        print("FAIL: promotion_eligible should be false.")
        return False
        
    print("SUCCESS: T00 baseline verified.")
    return True

if __name__ == "__main__":
    if not verify_latest_t00():
        sys.exit(1)
