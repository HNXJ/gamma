import os
import json
import subprocess
import hashlib
from datetime import datetime
import time

# Continuity Banner
BANNER = "Gamma Labyrinth is a continuous scientific-discovery game/world. truth_mode: truth_safe_unverified. truth_bearing_run: false. No biological/scientific truth asserted. No secrets."

def get_session_id():
    return datetime.now().strftime("%Y%m%dT%H%M%SZ")

def run_gemini(prompt):
    # Fixed: gemini.cmd on Windows requires shell=True
    try:
        result = subprocess.run(
            ["gemini", "-p", prompt, "-o", "json"],
            capture_output=True,
            text=True,
            shell=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Gemini error: {e}", flush=True)
        return None

def main():
    session_id = f"gemini_flash_lite_join_val_{get_session_id()}"
    base_dir = r"D:\workspace\gemini-gamma-labyrinth\runtime_artifacts\gamma\gemini_flash_lite_join_sessions"
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    print(f"Starting join validation run: {session_id}", flush=True)
    
    transcript = []
    hashes = {}
    
    mission_context = (
        "Mission: Gamma Labyrinth continuous scientific discovery game. "
        "Current mode: safe/spectator/player experience logging. "
        "No biological truth mutation. Reason scientifically, identify missions/patches, "
        "and preserve provenance."
    )
    
    for i in range(1, 6): # Validation run: 5 turns
        turn_id = f"turn_{i:04d}"
        print(f"Executing {turn_id}...", flush=True)
        
        prompt = mission_context if i == 1 else "Continue the scientific analysis and mission reasoning."
        if i == 1:
            prompt = f"{BANNER}\n\n{prompt}"
            
        response = run_gemini(prompt)
        if not response:
            print(f"Failed at {turn_id}")
            break
            
        # Redaction scan (mock)
        response_str = json.dumps(response)
        if "REDACT_ME" in response_str:
            response_str = response_str.replace("REDACT_ME", "[REDACTED]")
            response = json.loads(response_str)
            
        turn_file = os.path.join(session_dir, f"{turn_id}.json")
        with open(turn_file, "w") as f:
            json.dump(response, f, indent=2)
            
        # Record hash
        with open(turn_file, "rb") as f:
            hashes[f"{turn_id}.json"] = hashlib.sha256(f.read()).hexdigest()
            
        transcript.append({
            "turn": i,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "prompt": prompt,
            "response_summary": response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")[:100] + "..."
        })
        
        # Flush transcript
        with open(os.path.join(session_dir, "transcript.jsonl"), "a") as f:
            f.write(json.dumps(transcript[-1]) + "\n")
            
        time.sleep(1) # Rate limit friendly
        
    # Final artifacts
    with open(os.path.join(session_dir, "artifact_hashes.sha256"), "w") as f:
        for filename, h in hashes.items():
            f.write(f"{h}  {filename}\n")
            
    summary = {
        "session_id": session_id,
        "player_id": "gemini_flash_lite_external_001",
        "turns_completed": len(transcript),
        "truth_mode": "truth_safe_unverified",
        "status": "PASS" if len(transcript) == 40 else "PARTIAL"
    }
    
    with open(os.path.join(session_dir, "forty_turn_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
        
    receipt = {
        "type": "join_test_receipt",
        "session_id": session_id,
        "commit_decision": "OBSERVATION_ONLY",
        "no_truth_mutation": True,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(os.path.join(session_dir, "end_receipt.json"), "w") as f:
        json.dump(receipt, f, indent=2)
        
    print(f"Join test complete. Artifacts in {session_dir}")

if __name__ == "__main__":
    main()
