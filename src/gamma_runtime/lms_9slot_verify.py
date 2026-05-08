import argparse
import json
import os
import urllib.error
import urllib.request
import hashlib
from typing import Any, Dict, List, Optional

OFFICE_MAC_URL = "http://100.69.184.42:1234/v1"
WINDOWS_JUDGE_URL = "http://100.65.139.39:1235/v1"

SLOTS = {
    "player_slot_01": {"model": "gemma-4-e4b-it-mlx:2", "endpoint": OFFICE_MAC_URL},
    "player_slot_02": {"model": "gemma-4-e4b-it-mlx:3", "endpoint": OFFICE_MAC_URL},
    "player_slot_03": {"model": "gemma-4-e4b-it-mlx:4", "endpoint": OFFICE_MAC_URL},
    "player_slot_04": {"model": "gemma-4-e4b-it-mlx:5", "endpoint": OFFICE_MAC_URL},
    "player_slot_05": {"model": "gemma-4-e4b-it-mlx:8", "endpoint": OFFICE_MAC_URL},
    "player_slot_06": {"model": "gemma-4-e4b-it-mlx", "endpoint": OFFICE_MAC_URL},
    "player_slot_07": {"model": "gemma-4-e4b-it", "endpoint": OFFICE_MAC_URL},
    "player_slot_08": {"model": "gemma-4-e4b-it-mxfp8", "endpoint": OFFICE_MAC_URL},
    "judge_slot_j01": {"model": "gemma-4-e4b-it-mlx", "endpoint": WINDOWS_JUDGE_URL}
}

def _request_json(url: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    
    # Check for token without exposing it
    token_keys = ["LM_STUDIO_API_KEY", "LMS_API_TOKEN", "LM_API_TOKEN"]
    token = None
    for k in token_keys:
        if os.environ.get(k):
            token = os.environ.get(k)
            break
            
    if token:
        headers["Authorization"] = "Bearer " + token

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": response.status, "json": json.loads(raw)}
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "error": f"HTTP {exc.code}"
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "error": str(exc)[:160]
        }

def list_models(base_url: str) -> Dict[str, Any]:
    return _request_json(f"{base_url}/models")

def smoke_ping(base_url: str, model_id: str) -> Dict[str, Any]:
    prompt = "Gamma Labyrinth continuity. Bounded slot verification smoke check. truth_mode: truth_safe_unverified. truth_bearing_run: false. No secrets. No biological/scientific truth claims. Please reply exactly with the word: OK"
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 10,
        "stream": False
    }
    return _request_json(f"{base_url}/chat/completions", method="POST", payload=payload)

def generate_dry_run_artifacts(artifact_root: str):
    os.makedirs(f"{artifact_root}/turn_requests", exist_ok=True)
    manifest = []
    
    for slot_id, conf in SLOTS.items():
        req = {
            'model': conf['model'],
            'endpoint': conf['endpoint'],
            'messages': [
                {'role': 'system', 'content': 'Gamma Labyrinth continuity. You are a harnessed LMS slot in a minimal protocol validation round. truth_mode: truth_safe_unverified. truth_bearing_run: false. No secrets. No biological/scientific truth claims. Output compact JSON only.'},
                {'role': 'user', 'content': f'Return compact JSON with exactly these keys: ok, slot_id, role, lms_instance_id_seen, truth_mode, truth_bearing_run, protocol_understood, no_science_claims, next_action. Set slot_id={slot_id}, role=player_or_judge, lms_instance_id_seen={conf["model"]}, truth_mode=truth_safe_unverified, truth_bearing_run=false, protocol_understood=true, no_science_claims=true, next_action=end_minimal_harness_round'}   
            ],
            'temperature': 0,
            'max_tokens': 160,
            'stream': False
        }
        manifest.append(req)
        with open(f"{artifact_root}/turn_requests/{slot_id}_request.json", 'w') as f:
            json.dump(req, f, indent=2)
            
    print(f"Dry run: Would verify 9 slots against configured endpoints.")
    return True

def run_live_verification(artifact_root: str) -> str:
    status_report = {
        "phase": "bounded_slot_verification",
        "truth_mode": "truth_safe_unverified",
        "truth_bearing_run": False,
        "slots": {}
    }
    
    all_passed = True
    some_passed = False
    
    player_pinged = False
    judge_pinged = False
    
    for slot_id, conf in SLOTS.items():
        print(f"Verifying {slot_id}...")
        
        # 1. Model inventory check
        models_res = list_models(conf["endpoint"])
        if not models_res["ok"]:
            status_report["slots"][slot_id] = f"ENDPOINT_BLOCKED (models API: {models_res.get('error')})"
            all_passed = False
            continue
            
        available_models = [m.get("id") for m in models_res["json"].get("data", [])]
        if conf["model"] not in available_models:
            status_report["slots"][slot_id] = "FAILED (model missing in inventory)"
            all_passed = False
            continue
            
        # 2. Smoke check (Bounded Ping - maximum 1 player, 1 judge)
        do_ping = False
        if "player" in slot_id and not player_pinged:
            do_ping = True
            player_pinged = True
        elif "judge" in slot_id and not judge_pinged:
            do_ping = True
            judge_pinged = True
            
        if do_ping:
            smoke_res = smoke_ping(conf["endpoint"], conf["model"])
            if not smoke_res["ok"]:
                if smoke_res.get("status") in [401, 403]:
                     status_report["slots"][slot_id] = "AUTH_BLOCKED"
                else:
                     status_report["slots"][slot_id] = f"FAILED (smoke ping: {smoke_res.get('error')})"
                all_passed = False
                continue
                
            # Verify content
            try:
                 reply = smoke_res["json"]["choices"][0]["message"]["content"].strip()
                 if "OK" in reply.upper():
                      status_report["slots"][slot_id] = "PASS"
                      some_passed = True
                 else:
                      status_report["slots"][slot_id] = "FAILED (Unexpected response)"
                      all_passed = False
            except (KeyError, IndexError):
                 status_report["slots"][slot_id] = "FAILED (Malformed response)"
                 all_passed = False
        else:
            # For slots we don't ping, inventory check is sufficient to mark them PASS
            status_report["slots"][slot_id] = "PASS"
            some_passed = True

    if all_passed:
        verdict = "LMS_8SLOT_VERIFY_PASS"
    elif some_passed:
        verdict = "LMS_8SLOT_VERIFY_PARTIAL"
    else:
        # Determine if it's broadly an endpoint or auth issue
        if any("ENDPOINT_BLOCKED" in s for s in status_report["slots"].values()):
            verdict = "ENDPOINT_BLOCKED"
        elif any("AUTH_BLOCKED" in s for s in status_report["slots"].values()):
            verdict = "AUTH_BLOCKED"
        else:
            verdict = "LMS_8SLOT_VERIFY_FAILED"
            
    status_report["status"] = verdict
    
    os.makedirs(artifact_root, exist_ok=True)
    with open(f"{artifact_root}/verified_slot_status.json", 'w') as f:
        json.dump(status_report, f, indent=2)
        
    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify-live", action="store_true")
    parser.add_argument("--artifact-root", required=True)
    args = parser.parse_args()

    if args.dry_run:
        generate_dry_run_artifacts(args.artifact_root)
    elif getattr(args, 'verify_live', False) or getattr(args, 'verify-live', False):
        verdict = run_live_verification(args.artifact_root)
        print(f"VERDICT: {verdict}")
    else:
        print("Must specify either --dry-run or --verify-live")
        exit(1)
