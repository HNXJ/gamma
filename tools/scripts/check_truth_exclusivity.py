import os
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIFEST_PATH = os.path.join(ROOT, "context/governance/state_sensitivity.json")

def check():
    print(f"--- Truth Exclusivity Audit ---")
    if not os.environ.get("TRUTH_GATE_ENABLED") or not os.environ.get("AUTHORITY_TOKEN"):
        print("FAILED: Truth Gate not configured in environment.")
        sys.exit(1)
        
    if not os.path.exists(MANIFEST_PATH):
        print(f"FAILED: State manifest missing at {MANIFEST_PATH}")
        sys.exit(1)
        
    try:
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"FAILED: Could not parse state manifest: {e}")
        sys.exit(1)
        
    registry = manifest.get("registry", [])
    errors = 0
    
    for entry in registry:
        path = entry.get("path")
        if entry.get("truth_gate") == "Required":
            print(f"PASSED: [{path}] is Gated.")
        else:
            print(f"WARNING: [{path}] is UNGATED.")
            if entry.get("class") == "TRUTH_CANDIDATE":
                errors += 1
                print(f"FAILED: [{path}] is TRUTH_CANDIDATE but NOT GATED.")
                
    if errors > 0:
        print(f"\nAudit failed: {errors} ungated production write paths found.")
        sys.exit(1)
    else:
        print("\nVERIFIED: All truth-plane write paths are gated.")

if __name__ == "__main__":
    check()
