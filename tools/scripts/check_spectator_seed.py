import os
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SEED_PATH = os.path.join(ROOT, "context/pillars/spectator_seed.json")

def check():
    print(f"--- Spectator Seed Audit ---")
    if not os.path.exists(SEED_PATH):
        print(f"FAILED: Spectator seed missing at {SEED_PATH}")
        sys.exit(1)
        
    try:
        with open(SEED_PATH, 'r') as f:
            seed = json.load(f)
    except Exception as e:
        print(f"FAILED: Could not parse spectator seed: {e}")
        sys.exit(1)
        
    required_fields = [
        "pinned_message", 
        "queue_order", 
        "lobby_topics", 
        "initial_stack", 
        "world_baseline_summary"
    ]
    errors = 0
    
    for field in required_fields:
        if field not in seed:
            print(f"FAILED: Missing required field '{field}' in spectator seed.")
            errors += 1
        else:
            print(f"PASSED: Field '{field}' is present.")
            
    if errors > 0:
        print(f"Total Errors: {errors}")
        sys.exit(1)
    else:
        print("VERIFIED: Spectator room substrate is correctly seeded.")

if __name__ == "__main__":
    check()
