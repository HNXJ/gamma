import os
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKERS_PATH = os.path.join(ROOT, "context/pillars/workers.json")

def check():
    print(f"--- Safe Mode Config Audit ---")
    if not os.path.exists(WORKERS_PATH):
        print(f"FAILED: Workers config missing at {WORKERS_PATH}")
        sys.exit(1)
        
    try:
        with open(WORKERS_PATH, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"FAILED: Could not parse workers config: {e}")
        sys.exit(1)
        
    workers = config.get("workers", [])
    errors = 0
    
    # Check for mandatory pillars
    required_pillars = {"tunnel", "heartbeat", "safety"}
    found_pillars = set()
    
    for w in workers:
        name = w.get("name")
        safe_req = w.get("safe_mode_required", False)
        mandatory = w.get("mandatory_pillar", False)
        
        if name in required_pillars:
            if not safe_req or not mandatory:
                print(f"FAILED: Worker '{name}' is a required pillar but is not marked as mandatory/safe-mode-required.")
                errors += 1
            else:
                found_pillars.add(name)
                print(f"PASSED: Pillar '{name}' is correctly hardened.")
        else:
            print(f"INFO: Worker '{name}' (Optional/Control)")

    missing = required_pillars - found_pillars
    if missing:
        print(f"FAILED: Missing mandatory pillars in config: {missing}")
        errors += 1
        
    if errors > 0:
        print(f"Total Errors: {errors}")
        sys.exit(1)
    else:
        print("VERIFIED: Safe Mode configuration is resilient.")

if __name__ == "__main__":
    check()
