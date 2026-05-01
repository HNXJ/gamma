import os
import json
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIFEST_PATH = os.path.join(ROOT, "context/governance/code_sensitivity.json")

def check():
    print(f"--- Code Sensitivity Audit ---")
    if not os.path.exists(MANIFEST_PATH):
        print(f"FAILED: Manifest missing at {MANIFEST_PATH}")
        sys.exit(1)
        
    try:
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"FAILED: Could not parse manifest: {e}")
        sys.exit(1)
        
    registry = manifest.get("registry", [])
    errors = 0
    coverage = {}
    
    for entry in registry:
        path = entry.get("path")
        level = entry.get("level")
        full_path = os.path.join(ROOT, path)
        
        coverage[level] = coverage.get(level, 0) + 1
        
        if not os.path.exists(full_path):
            print(f"FAILED: [{level}] {path} - File missing!")
            errors += 1
            continue
            
        if level == "PILLAR":
            # Check for banner
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    if "PILLAR : WARNING" not in content:
                        print(f"FAILED: [{level}] {path} - Missing PILLAR : WARNING banner!")
                        errors += 1
                    else:
                        print(f"PASSED: [{level}] {path}")
            except Exception as e:
                print(f"FAILED: [{level}] {path} - Could not read: {e}")
                errors += 1
        else:
            print(f"PASSED: [{level}] {path}")

    print(f"\nAudit Summary:")
    print(f"Coverage: {coverage}")
    if errors > 0:
        print(f"Total Errors: {errors}")
        sys.exit(1)
    else:
        print("VERIFIED: All classified files present and pillars guarded.")

if __name__ == "__main__":
    check()
