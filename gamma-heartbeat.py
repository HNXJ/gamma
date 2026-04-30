import time
import json
import os
import requests
import logging
import fcntl
from datetime import datetime

# Config Doctrine: Use local internal service surfaces
from src.gamma_runtime.config import (
    get_lms_local_url, 
    get_hub_local_url, 
    detect_lms_connectivity_mode,
    LMSConnectivityMode
)
from src.gamma_runtime.spectator_room import SpectatorRoom

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
LOCK_FILE = os.path.join(ROOT, "local/run/heartbeat.lock")

def check_lms():
    try:
        resp = requests.get(f"{LMS_URL}/v1/models", timeout=2)
        return "ALIVE" if resp.status_code == 200 else "DEGRADED"
    except:
        return "CRASHED"

def get_lms_models():
    try:
        resp = requests.get(f"{LMS_URL}/v1/models", timeout=2)
        if resp.status_code == 200:
            return [m['id'] for m in resp.json().get('data', [])]
    except:
        pass
    return []

def check_hub():
    try:
        resp = requests.get(f"{HUB_URL}/sessions", timeout=2)
        return "ALIVE" if resp.status_code == 200 else "DEGRADED"
    except:
        return "CRASHED"

def check_events():
    if not os.path.exists(EVENTS_FILE):
        return "STALLED"
    try:
        mtime = os.path.getmtime(EVENTS_FILE)
        if time.time() - mtime > 60: # No events for 1 minute
            return "STALLED"
        return "ALIVE"
    except:
        return "STALLED"

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
                if name != "orchestrator": # Orchestrator expected dead in safe mode
                    logger.warning(f"Worker {name} (PID {pid}) is not running.")
                    return "DEGRADED"
        return "ALIVE"
    except:
        return "CRASHED"

def process_spectator_turn(room, available_models):
    speaker = room.get_current_speaker(available_models)
    if not speaker:
        logger.info("Spectator Loop: Waiting for at least 2 models.")
        return

    top_item = room.get_top_of_stack()
    
    # Identify the best matching model ID from available ones
    target_model = available_models[0] # Default to first
    for m in available_models:
        if any(part.lower() in m.lower() for part in speaker.split('-')):
            target_model = m
            break

    prompt = f"""
    [SPECTATOR ROOM ROLE: {speaker}]
    
    Current World State (Top of Stack):
    ---
    {top_item}
    ---
    
    Task: Read the current state above. Provide one concise reflection (2-3 sentences) on the current progress or world logic from your specific perspective as {speaker}. 
    Then, summarize the updated world state for the next agent in the relay.
    
    FORMAT:
    Reflection: <your reflection>
    Updated State: <summary of progress + your contribution>
    """
    
    try:
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        logger.info(f"Spectator Turn: Requesting inference from {speaker} (via {target_model})")
        resp = requests.post(f"{LMS_URL}/v1/chat/completions", json=payload, timeout=60)
        if resp.status_code == 200:
            result = resp.json()['choices'][0]['message']['content']
            
            reflection = ""
            updated_state = ""
            if "Reflection:" in result and "Updated State:" in result:
                parts = result.split("Updated State:")
                reflection = parts[0].replace("Reflection:", "").strip()
                updated_state = parts[1].strip()
            else:
                reflection = result[:200]
                updated_state = result
                
            room.post_turn(speaker, reflection, updated_state)
            logger.info(f"Spectator Turn: {speaker} completed. Stack advanced.")
        else:
            logger.error(f"Spectator turn failed for {speaker}: LMS returned {resp.status_code}")
    except Exception as e:
        logger.error(f"Spectator turn failed for {speaker}: {e}")

def run_pulse():
    safe_mode = os.environ.get("SAFE_MODE", "true").lower() == "true"
    room = SpectatorRoom(ROOT)
    
    # Ensure lock directory exists
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    lock_fd = open(LOCK_FILE, "w")

    while True:
        try:
            # Try to acquire an exclusive lock without blocking
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            time.sleep(1)
            continue
            
        try:
            lms_status = check_lms()
            lms_mode = detect_lms_connectivity_mode()
            available_models = get_lms_models() if lms_status == "ALIVE" else []
            
            # Spectator Loop
            if safe_mode and lms_mode in [LMSConnectivityMode.LOCAL, LMSConnectivityMode.TUNNELED]:
                if len(available_models) >= 2:
                    process_spectator_turn(room, available_models)
                else:
                    room.set_status("WAITING_FOR_PLAYERS")
            elif lms_mode == LMSConnectivityMode.UNAVAILABLE:
                room.set_status("LMS_UNAVAILABLE")

            health = {
                "timestamp": datetime.now().isoformat(),
                "lms": lms_status,
                "lms_connectivity_mode": lms_mode.value,
                "hub": check_hub(),
                "events": check_events(),
                "workers": check_pids(),
                "safe_mode_running": safe_mode,
                "full_mode_ready": lms_mode != LMSConnectivityMode.UNAVAILABLE,
                "spectator_room": room.get_board()["status"]
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
                
            logger.info(f"Health Pulse: {health['status']} | LMS: {health['lms']} ({health['lms_connectivity_mode']}) | Spectator: {health['spectator_room']}")
            
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
        finally:
            # Release the lock
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
                
        time.sleep(5)

if __name__ == "__main__":
    run_pulse()
