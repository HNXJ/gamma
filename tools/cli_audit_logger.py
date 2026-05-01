import json, os, hashlib
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(BASE_DIR, "local", "run", "cli_audit.jsonl")
SUMMARY_PATH = os.path.join(BASE_DIR, "local", "run", "cli_audit_summary_latest.json")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def redact(s):
    if not isinstance(s, str): return s
    secrets = ["TOKEN", "PASSWORD", "COOKIE", "AUTH", "SECRET"]
    for secret in secrets:
        if secret in s.upper(): return "[REDACTED]"
    return s

def log_event(event_data):
    event_data['ts'] = datetime.now().isoformat()
    content_to_hash = {k: v for k, v in event_data.items() if k != 'hash'}
    event_str = json.dumps(content_to_hash, sort_keys=True)
    event_data['hash'] = hashlib.sha256(event_str.encode()).hexdigest()
    
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            if lines and json.loads(lines[-1]).get('hash') == event_data['hash']:
                return
    
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(event_data) + "\n")
    
    events = [json.loads(l) for l in (open(LOG_PATH, "r").readlines())]
    with open(SUMMARY_PATH, "w") as f:
        json.dump({"total_events": len(events), "last_update": datetime.now().isoformat()}, f)
