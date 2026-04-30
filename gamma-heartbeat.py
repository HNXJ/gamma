import time
import json
import os
import requests
import logging
from datetime import datetime

# Config Doctrine: Use local internal service surfaces
from src.gamma_runtime.config import get_lms_local_url, get_hub_local_url

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HEARTBEAT] %(levelname)s: %(message)s'
)
logger = logging.getLogger("GammaHeartbeat")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
HUB_URL = get_hub_local_url()
LMS_URL = get_lms_local_url()
HEALTH_FILE = os.path.join(ROOT, "local/run/health.json")
PID_FILE = os.path.join(ROOT, "local/run/pids.json")
EVENTS_FILE = os.path.join(ROOT, "local/events.jsonl")

def check_lms():
    try:
        resp = requests.get(f"{LMS_URL}/v1/models", timeout=2)
        return "ALIVE" if resp.status_code == 200 else "DEGRADED"
    except:
        return "CRASHED"

def check_hub():
    try:
        resp = requests.get(f"{HUB_URL}/sessions", timeout=2)
        return "ALIVE" if resp.status_code == 200 else "DEGRADED"
    except:
        return "CRASHED"

def check_events():
    if not os.path.exists(EVENTS_FILE):
        return "STALLED"
    mtime = os.path.getmtime(EVENTS_FILE)
    if time.time() - mtime > 60: # No events for 1 minute
        return "STALLED"
    return "ALIVE"

def check_pids():
    if not os.path.exists(PID_FILE):
        return "CRASHED"
    try:
        with open(PID_FILE, 'r') as f:
            pids = json.load(f)
        for name, pid in pids.items():
            try:
                os.kill(pid, 0)
            except OSError:
                logger.warning(f"Worker {name} (PID {pid}) is not running.")
                return "DEGRADED"
        return "ALIVE"
    except:
        return "CRASHED"

def run_pulse():
    while True:
        health = {
            "timestamp": datetime.now().isoformat(),
            "lms": check_lms(),
            "hub": check_hub(),
            "events": check_events(),
            "workers": check_pids()
        }
        
        values = list(health.values())
        if "CRASHED" in values:
            health["status"] = "CRASHED"
        elif "STALLED" in values or "DEGRADED" in values:
            health["status"] = "DEGRADED"
        else:
            health["status"] = "ALIVE"
            
        with open(HEALTH_FILE, 'w') as f:
            json.dump(health, f, indent=2)
            
        logger.info(f"Health Pulse: {health['status']} | LMS: {health['lms']} | Hub: {health['hub']} | Workers: {health['workers']}")
        
        if health["hub"] == "ALIVE":
            try:
                requests.post(f"{HUB_URL}/events", json={
                    "agent_id": "HEARTBEAT",
                    "role": "monitor",
                    "event_type": "health_pulse",
                    "summary": f"System status: {health['status']}",
                    "status": health["status"],
                    "metadata": health
                }, timeout=1)
            except:
                pass
                
        time.sleep(5)

if __name__ == "__main__":
    run_pulse()
