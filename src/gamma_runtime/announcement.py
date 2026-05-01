import os
import json
import time
import requests
import sys
from datetime import datetime
from typing import Dict, Any, List

# Stable port config
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(ROOT, "context/runtime/ports.json")
RELAY_LOCK = os.path.join(ROOT, "local/run/relay.lock")

class AnnouncementEngine:
    @staticmethod
    def resolve_lms_endpoint() -> Dict[str, Any]:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        canonical_port = config['ports']['lms']
        # Try LOCAL
        try:
            r = requests.get(f"http://localhost:{canonical_port}/v1/models", timeout=2)
            if r.status_code == 200:
                return {"canonical_port": canonical_port, "access_mode": "LOCAL", "resolved_endpoint": f"http://localhost:{canonical_port}"}
        except: pass
        
        # Try REMOTE (Office Mac)
        remote_ep = config['runtime_resolution']['resolved_lms_endpoint']
        try:
            r = requests.get(f"{remote_ep}/v1/models", timeout=5)
            if r.status_code == 200:
                return {"canonical_port": canonical_port, "access_mode": "REMOTE_ONLY", "resolved_endpoint": remote_ep}
        except: pass
        
        return {"access_mode": "UNPROVEN"}

    @staticmethod
    def pause_relay():
        with open(RELAY_LOCK, "w") as f: f.write("PAUSED")
        
    @staticmethod
    def resume_relay():
        if os.path.exists(RELAY_LOCK): os.remove(RELAY_LOCK)

    @staticmethod
    def run_announcement_test(aid: str, isolation: bool = True):
        if isolation: AnnouncementEngine.pause_relay()
        try:
            endpoint = AnnouncementEngine.resolve_lms_endpoint()
            if endpoint.get("access_mode") == "UNPROVEN": raise Exception("LMS Unproven")
            
            announcement = {
                "announcement_id": aid,
                "timestamp": datetime.now().isoformat(),
                "body": "State your exact model identifier, role, and one sentence on current room state."
            }
            models = ["G01-builder", "G02-tuner", "G03-analyst", "J01-judge", "M01-monitor"]
            
            results = []
            for mid in models:
                try:
                    resp = requests.post(f"{endpoint['resolved_endpoint']}/v1/chat/completions", json={
                        "model": mid,
                        "messages": [{"role": "user", "content": announcement["body"]}]
                    }, timeout=10)
                    results.append({"model_id": mid, "data": resp.json(), "verdict": "ACKNOWLEDGED"})
                except Exception as e:
                    results.append({"model_id": mid, "error": str(e), "verdict": "FAIL"})
            
            # Persist artifacts
            with open(f"local/run/announcement_test_{aid}.json", "w") as f: json.dump(results, f)
            return results
        finally:
            if isolation: AnnouncementEngine.resume_relay()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--announcement-id", default=f"TEST_{int(time.time())}")
    parser.add_argument("--pause-relay", action="store_true")
    args = parser.parse_args()
    
    if args.mode == "resolve": print(AnnouncementEngine.resolve_lms_endpoint())
    elif args.mode == "announce": print(AnnouncementEngine.run_announcement_test(args.announcement_id, args.pause_relay))
