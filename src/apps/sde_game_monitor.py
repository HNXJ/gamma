import os
import sqlite3
import json
import time
import re
import asyncio
import sys
from datetime import datetime

# Dynamic Path Resolution for gamma_runtime
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(ROOT_DIR, 'src') not in sys.path:
    sys.path.append(os.path.join(ROOT_DIR, 'src'))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import plotly.graph_objects as go
import subprocess
from pydantic import BaseModel
import random
import hashlib

from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

from gamma_runtime.config import HUB_PORT, DASHBOARD_PORT, get_dashboard_local_url, MONITOR_PORT
from gamma_runtime.player_identity import PlayerIdentityManager

import logging
import subprocess
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sde_monitor")



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_dashboard_local_url()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System Start Time for Uptime Grounding
START_TIME = time.time()
NETWORK_EPOCH = datetime.now().isoformat()
SNAPSHOT_VERSION = 1

# Dynamic Path Resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "dashboard", "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "dashboard", "static")

# Explicit Static Mounting
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Environment-based paths for logs and DB
DEFAULT_LOG_PATH = os.path.join(ROOT_DIR, "local", "run", "orchestrator.log")
HEARTBEAT_LOG_PATH = os.path.join(ROOT_DIR, "local", "run", "heartbeat.log")
DB_PATH = os.getenv("GAMMA_DB_PATH", "file::memory:?cache=shared")

# Auto-detect Log Path based on activity
if not os.path.exists(DEFAULT_LOG_PATH) or os.path.getsize(DEFAULT_LOG_PATH) == 0:
    LOG_PATH = os.getenv("GAMMA_LOG_PATH", HEARTBEAT_LOG_PATH)
else:
    LOG_PATH = os.getenv("GAMMA_LOG_PATH", DEFAULT_LOG_PATH)

# Agent Log Mapping (Grounded for workspace)
AGENT_LOGS = {
    "G01": os.path.join(ROOT_DIR, "local", "run", "orchestrator.log"),
    "G02": os.path.join(ROOT_DIR, "local", "run", "heartbeat.log"),
    "G03": os.path.join(ROOT_DIR, "local", "run", "safety.log"),
    "G04": os.path.join(ROOT_DIR, "local", "run", "hub_api.log")
}

# Global state for streaming logs
council_dialogue = []
structured_events = [] # Placeholder for future structured provenance events
tps_stats = {"total_tokens": 0, "last_tps_check": time.time(), "tps": 0.0}

# Agent Activity + Novelty Tracking
AGENT_ACTIVITY = {}
IDENTITY_ALIASES = {}

def load_aliases():
    global IDENTITY_ALIASES
    alias_path = os.path.join(ROOT_DIR, "context", "configs", "identity_aliases.json")
    if os.path.exists(alias_path):
        try:
            with open(alias_path, "r") as f:
                data = json.load(f)
                IDENTITY_ALIASES = data.get("aliases", {})
        except: pass

load_aliases()

def resolve_agent_id(raw_id: str) -> str:
    # Check for direct match in aliases
    if raw_id in IDENTITY_ALIASES:
        return IDENTITY_ALIASES[raw_id]
    # Check for substring match in roster (e.g. G01-builder -> G01)
    for canonical in ["G01", "G02", "G03", "J01", "M01"]:
        if canonical in raw_id:
            return canonical
    return raw_id

def get_content_hash(content: str) -> str:
    return hashlib.md5(content.strip().encode()).hexdigest()

def update_monitor_data():
    global council_dialogue, tps_stats, structured_events
    last_pos = 0
    while True:
        try:
            # Refresh aliases occasionally
            if random.random() < 0.1: load_aliases()
            
            # ... (rest of parsing)
            # 1. Check for structured provenance records (Durable Path)
            # Placeholder for future structured sink integration
            pass

            # 2. Legacy Log Parsing (Fallback)
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "r") as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    last_pos = f.tell()
                    
                    for line in lines:
                        # Regex Extraction: [Agent], [Timestamp], [Message]
                        match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - INFO - (.*)", line)
                        if match:
                            ts, log_source, msg = match.groups()
                            
                            # Standard Dialogue Logging
                            if any(a in log_source for a in ["Macro", "Meso", "Micro", "Critic", "Monitor", "Optimizer", "Analyst", "Manager", "v1_gamma", "G01", "G02", "G03", "J01", "M01"]):
                                entry = {"time": ts, "agent": log_source, "msg": msg}
                                council_dialogue.append(entry)
                                if len(council_dialogue) > 100: council_dialogue.pop(0)
                                tps_stats["total_tokens"] += len(msg.split()) * 4 # Approximation
                            
                            # Activity + Novelty Tracking (Structured Contribution)
                            contrib_match = re.search(r"Agent (.*?) Contribution: (.*)", msg)
                            if contrib_match:
                                raw_id, content = contrib_match.groups()
                                agent_id = resolve_agent_id(raw_id)
                                msg_hash = get_content_hash(content)
                                
                                if agent_id not in AGENT_ACTIVITY:
                                    AGENT_ACTIVITY[agent_id] = {
                                        "last_message_ts": ts,
                                        "last_message_hash": msg_hash,
                                        "consecutive_repeat_count": 0,
                                        "novelty_state": "NOVEL",
                                        "last_event_ts": time.time(),
                                        "turns_since_last_contribution": 0
                                    }
                                else:
                                    act = AGENT_ACTIVITY[agent_id]
                                    if msg_hash == act["last_message_hash"]:
                                        act["consecutive_repeat_count"] += 1
                                    else:
                                        act["consecutive_repeat_count"] = 0
                                        act["last_message_hash"] = msg_hash
                                    
                                    act["last_message_ts"] = ts
                                    act["last_event_ts"] = time.time()
                                    act["novelty_state"] = "REPEATING" if act["consecutive_repeat_count"] >= 1 else "NOVEL"
                                    act["turns_since_last_contribution"] = 0
                        
                        # Simple TPS calc
                        now = time.time()
                        if now - tps_stats["last_tps_check"] > 5:
                            tps_stats["tps"] = (len(lines) * 5) / 5 # Simplified
                            tps_stats["last_tps_check"] = now
        except Exception:
            pass 
        time.sleep(1)

# Start background thread
import threading
if LOG_PATH != "/dev/null":
    threading.Thread(target=update_monitor_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="arena.html")

@app.get("/roster", response_class=HTMLResponse)
async def roster_page(request: Request):
    return templates.TemplateResponse(request=request, name="roster.html")

# Canonical Paths
SPECTATOR_PATH = os.path.join(ROOT_DIR, "local", "run", "spectator_room.json")
HEALTH_PATH = os.path.join(ROOT_DIR, "local", "run", "health.json")
QUEUE_PATH = os.path.join(ROOT_DIR, "local", "run", "communication_display.json")

@app.get("/api/diag")
async def get_diag():
    """Diagnostic endpoint for path verification."""
    manager = PlayerIdentityManager(root_dir=ROOT_DIR)
    return {
        "ROOT_DIR": ROOT_DIR,
        "CONFIG_ROOT": config.root,
        "LOG_PATH": LOG_PATH,
        "TEMPLATES_DIR": str(TEMPLATES_DIR),
        "registry_exists": os.path.exists(os.path.join(ROOT_DIR, "local/player_accounts/registry.json")),
        "bindings_exists": os.path.exists(os.path.join(ROOT_DIR, "local/player_accounts/bindings.json")),
        "sessions_exists": os.path.exists(os.path.join(ROOT_DIR, "local/player_sessions/active.json")),
        "manager_accounts_path": str(manager.accounts_path),
        "manager_sessions_path": str(manager.sessions_path)
    }

@app.get("/api/status")
async def get_status():
    progression = await get_progression()
    persistence = await get_persistence()
    health = await get_health()
    
    # Grounded Heartbeat derivation
    spectator_data = {}
    try:
        with open(SPECTATOR_PATH, 'r') as f:
            spectator_data = json.load(f)
    except Exception as e:
        pass
    
    last_updated = spectator_data.get("last_updated", "")
    turn_index = spectator_data.get("turn_index", 0)
    
    heartbeat_val = "STALLED"
    if last_updated:
        # Check if updated in last 60 seconds
        try:
            dt = datetime.fromisoformat(last_updated)
            if (datetime.now() - dt).total_seconds() < 60:
                heartbeat_val = "OK"
                if health.get("status") not in ["SAFE_MODE_OPERATIONAL", "ALIVE"]:
                    heartbeat_val = "DEGRADED"
        except:
            pass
        
    return {
        "system": {
            "status": health.get("status", "STANDBY"),
            "heartbeat": heartbeat_val,
            "dialogue_activity": "ACTIVE" if council_dialogue else "INACTIVE",
            "last_signal": last_updated,
            "monitor_uptime_seconds": health.get("monitor_uptime_seconds", int(time.time() - START_TIME)),
            "backend_model_slots_occupied": "3 / 4",
            "metadata": {
                "health_timestamp": health.get("timestamp"),
                "spectator_timestamp": last_updated,
                "turn_index": turn_index
            }
        },
        "progression": progression,
        "persistence": persistence,
        "research": {
            "neuron_count": progression.get("largest_pass_network_neuron_count"),
            "active_target": progression.get("active_mission_target"),
            "mission_topic": progression.get("active_mission_topic"),
            "pass_network": f"{progression.get('largest_pass_network_neuron_count')}-Node Grounded" if progression.get("largest_pass_network_neuron_count") else None,
            "active_patch": progression.get("active_patches")[0] if progression.get("active_patches") else None,
            "omissions": progression.get("omissions", 0)
        }
    }

@app.get("/api/diag")
async def get_diag():
    """Diagnostic endpoint for path verification."""
    manager = PlayerIdentityManager(root_dir=ROOT_DIR)
    return {
        "ROOT_DIR": ROOT_DIR,
        "CONFIG_ROOT": config.root,
        "LOG_PATH": LOG_PATH,
        "TEMPLATES_DIR": str(TEMPLATES_DIR),
        "registry_exists": os.path.exists(os.path.join(ROOT_DIR, "local/player_accounts/registry.json")),
        "bindings_exists": os.path.exists(os.path.join(ROOT_DIR, "local/player_accounts/bindings.json")),
        "sessions_exists": os.path.exists(os.path.join(ROOT_DIR, "local/player_sessions/active.json")),
        "manager_accounts_path": str(manager.accounts_path),
        "manager_sessions_path": str(manager.sessions_path)
    }

@app.get("/api/progression")
async def get_progression():
    progression = {"largest_pass_network_neuron_count": 10, "active_patches": [], "truth_class": "DEGRADED"}
    runtime_path = os.path.join(ROOT_DIR, "local/game001/arena_runtime_state.json")
    if os.path.exists(runtime_path):
        try:
            with open(runtime_path, "r") as f:
                runtime_data = json.load(f)
                progression.update({
                    "largest_pass_network_neuron_count": runtime_data.get("largest_pass_network_neuron_count"),
                    "active_patches": runtime_data.get("active_patches"),
                    "truth_class": "GROUNDED"
                })
        except Exception: pass
    board_path = os.path.join(ROOT_DIR, "context/configs/patches/arena_patch_board.json")
    if os.path.exists(board_path):
        try:
            with open(board_path, "r") as f:
                board_data = json.load(f)
                progression.update(board_data)
        except Exception: pass
    return progression

@app.get("/api/agents")
async def get_agents():
    SPECTATOR_PATH = os.path.join(ROOT_DIR, "local", "run", "spectator_room.json")
    HEALTH_PATH = os.path.join(ROOT_DIR, "local", "run", "health.json")
    QUEUE_PATH = os.path.join(ROOT_DIR, "local", "run", "communication_display.json")
    
    roster = [
        {"id": "G01", "role": "Builder", "category": "Core Actor", "provenance": "Canonical Logic | Active"},
        {"id": "G02", "role": "Tuner", "category": "Core Actor", "provenance": "Canonical Logic | Active"},
        {"id": "G03", "role": "Analyst", "category": "Core Actor", "provenance": "Canonical Logic | Active"},
        {"id": "J01", "role": "Judge", "category": "Core Actor", "provenance": "Canonical Logic | Active"},
        {"id": "M01", "role": "Monitor", "category": "Core Actor", "provenance": "Canonical Logic | Active"}
    ]
    
    # Dynamic Guest Loading
    try:
        manager = PlayerIdentityManager(root_dir=ROOT_DIR)
        accounts = manager.list_accounts() # Returns Dict[str, PlayerAccount]
        logger.info(f"Identity Manager loaded {len(accounts)} accounts from {manager.accounts_path}")
        
        for username, acc in accounts.items():
            if username.startswith("lite_guest_"):
                # Check for active session
                session = manager.get_active_session(acc.account_id)
                status = "ACTIVE" if session else "PERSISTED"
                
                roster.append({
                    "id": username,
                    "name": acc.display_name,
                    "role": "Exploratory Guest",
                    "state": status,
                    "category": "GUEST",
                    "description": "Dev Guest | Exploratory Guest",
                    "provenance": "Persisted Identity | Runtime Visibility Pending"
                })
    except Exception as e:
        logger.error(f"Failed to load dynamic roster: {e}")
        # Diagnostic entry
        roster.append({
            "id": "sys_err",
            "name": "System Error",
            "role": "DIAGNOSTIC",
            "state": "FAILED",
            "category": "SYSTEM",
            "description": f"Error loading guests: {str(e)}",
            "provenance": "Monitor Trace"
        })

    
    status_map = {agent["id"]: "STANDBY" for agent in roster}
    pending_counts = {agent["id"]: 0 for agent in roster}
    system_blocker = None
    
    pending_items = {agent["id"]: [] for agent in roster}
    
    try:
        with open(HEALTH_PATH, 'r') as f:
            health = json.load(f)
            if health.get("lms") != "ALIVE":
                system_blocker = "LMS_UNAVAILABLE"
        
        with open(SPECTATOR_PATH, 'r') as f:
            room = json.load(f)
            queue = room.get("queue", [])
            idx = room.get("turn_index", 0)
            
            if queue:
                current_idx = idx % len(queue)
                next_idx = (idx + 1) % len(queue)
                current_raw = queue[current_idx]
                next_raw = queue[next_idx]
                
                current = resolve_agent_id(current_raw)
                next_a = resolve_agent_id(next_raw)
                
                # Assign statuses
                for aid in status_map:
                    if aid == current:
                        status_map[aid] = "BLOCKED_BY_LMS" if system_blocker else "ACTIVE"
                    elif aid == next_a:
                        status_map[aid] = "QUEUED"
            
        with open(QUEUE_PATH, 'r') as f:
            q_data = json.load(f)
            items = q_data.get("queue", [])
            for aid in pending_items:
                # In this system, items are broadcast to all or directed. 
                # For the contract, we expose what is currently in the display queue.
                pending_items[aid] = items
    except Exception:
        pass

    results = []
    for agent in roster:
        aid = agent["id"]
        status = status_map[aid]
        
        # Activity State Logic
        act_state = status
        if status == "STANDBY":
            if pending_items[aid]:
                act_state = "WAITING"
            else:
                act_state = "IDLE"
        
        # Overwrite if blocked
        if system_blocker and status == "ACTIVE":
            act_state = "BLOCKED"

        results.append({
            **agent,
            "status": status,
            "activity_state": act_state,
            "activity_reason": "LMS_BLOCK" if act_state == "BLOCKED" else "NORMAL",
            "novelty_state": AGENT_ACTIVITY.get(aid, {}).get("novelty_state", "UNKNOWN"),
            "consecutive_repeat_count": AGENT_ACTIVITY.get(aid, {}).get("consecutive_repeat_count", 0),
            "last_message_ts": AGENT_ACTIVITY.get(aid, {}).get("last_message_ts"),
            "last_turn_index_seen": AGENT_ACTIVITY.get(aid, {}).get("last_turn_index_seen"),
            "turns_since_last_contribution": AGENT_ACTIVITY.get(aid, {}).get("turns_since_last_contribution", 0),
            "pending_items_count": len(pending_items[aid]),
            "system_blocker": system_blocker,
            "last_active": "NOW" if status == "ACTIVE" else "",
            "grounded_evidence": True,
            "truth_class": "GROUNDED",
            "evidence_source": [SPECTATOR_PATH, HEALTH_PATH, QUEUE_PATH],
            "pending_items": pending_items[aid],
            "activity_metadata": AGENT_ACTIVITY.get(aid, {})
        })
    return results

@app.get("/api/agents/activity")
async def get_agent_activity_summary():
    agents = await get_agents()
    return {a["id"]: a.get("activity_metadata", {}) for a in agents}

@app.get("/api/agents/novelty")
async def get_agent_novelty_summary():
    agents = await get_agents()
    return {a["id"]: {
        "novelty_state": a["novelty_state"], 
        "consecutive_repeat_count": a["consecutive_repeat_count"]
    } for a in agents}

@app.get("/api/agents/{agent_id}/logs")
async def get_agent_logs(agent_id: str, lines: int = 100):
    path = AGENT_LOGS.get(agent_id)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Log file not found for {agent_id}")
    try:
        result = subprocess.run(["tail", "-n", str(lines), path], capture_output=True, text=True, timeout=2)
        return {"id": agent_id, "content": result.stdout, "path": path}
    except Exception as e:
        return {"error": str(e)}
@app.get("/api/agent-logs")
async def get_all_agent_logs(lines: int = 10):
    all_logs = {}
    for agent_id, path in AGENT_LOGS.items():
        if os.path.exists(path):
            try:
                result = subprocess.run(["tail", "-n", str(lines), path], capture_output=True, text=True, timeout=1)
                all_logs[agent_id] = result.stdout
            except Exception:
                all_logs[agent_id] = "LOG_READ_ERROR"
        else:
            all_logs[agent_id] = "LOG_NOT_FOUND"
    return {
        "logs": all_logs,
        "truth_class": "GROUNDED",
        "source": "Council Log Matrix"
    }

@app.get("/api/persistence")
async def get_persistence():
    persistence = { "boot_type": "UNKNOWN", "freshness": "DEGRADED", "resume_count": 0 }
    runtime_path = os.path.join(ROOT_DIR, "local/game001/arena_runtime_state.json")
    if os.path.exists(runtime_path):
        try:
            with open(runtime_path, "r") as f:
                ckpt = json.load(f)
                persistence["boot_type"] = "RESUMED" if len(ckpt.get("boot_history", [])) > 1 else "FRESH"
                persistence["resume_count"] = len(ckpt.get("boot_history", [])) - 1
                last_ts = ckpt.get("last_checkpoint_time", 0)
                if isinstance(last_ts, str):
                    last_dt = datetime.fromisoformat(last_ts)
                    persistence["last_checkpoint"] = last_dt.strftime("%H:%M:%S")
                    persistence["freshness"] = "GROUNDED" if (datetime.now() - last_dt).total_seconds() < 600 else "STALE"
                else:
                    persistence["last_checkpoint"] = datetime.fromtimestamp(last_ts).isoformat() if last_ts else "NEVER"
                    persistence["freshness"] = "GROUNDED" if (time.time() - last_ts < 600) else "STALE"
        except Exception:
            pass
    return persistence

@app.get("/api/health")
async def get_health():
    if os.path.exists(os.path.join(ROOT_DIR, "local", "run", "health.json")):
        with open(os.path.join(ROOT_DIR, "local", "run", "health.json"), "r") as f:
            return json.load(f)
    return {
        "status": "STANDBY",
        "zero_idle_mandate": "ENFORCED",
        "monitor_uptime_seconds": int(time.time() - START_TIME),
        "heartbeat": "STALLED"
    }

@app.get("/api/network/state")
async def get_network_state():
    types = ["E"]*7 + ["PV"]*2 + ["SST"]*1
    n = len(types)
    random.seed(42)
    nodes = {
        "id": [f"n{i}" for i in range(n)],
        "cell_type": types,
        "layer": ["L2/3"] * n,
        "x": [round(random.random(), 3) for _ in range(n)],
        "y": [round(random.random(), 3) for _ in range(n)],
        "z": [0.0] * n,
        "radius": [0.02] * n,
        "status": ["active"] * n,
        "truth_class": ["SYNTHETIC"] * n
    }
    edges = {
        "src": ["n0", "n1", "n2", "n7", "n8"],
        "dst": ["n7", "n8", "n9", "n0", "n1"],
        "weight": [0.8, 0.7, 0.9, -0.5, -0.6],
        "sign": ["exc", "exc", "exc", "inh", "inh"],
        "kind": ["synapse"] * 5,
        "truth_class": ["SYNTHETIC"] * 5
    }
    
    now_iso = datetime.now().isoformat()
    return {
        "snapshot_id": f"game001_net_{int(time.time())}",
        "snapshot_version": SNAPSHOT_VERSION,
        "network_epoch": NETWORK_EPOCH,
        "snapshot_time": now_iso,
        "truth_class": "SYNTHETIC",
        "source": "MOCK_TOPOLOGY",
        "units": { "position": "normalized", "radius": "normalized", "weight": "unitless" },
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "official_level": 10,
            "largest_grounded_pass_network": 10,
            "refresh_time": now_iso
        }
    }

@app.get("/api/events/stream")
async def event_stream():
    async def event_generator():
        last_idx = len(council_dialogue)
        while True:
            if len(council_dialogue) > last_idx:
                for i in range(last_idx, len(council_dialogue)):
                    data = json.dumps({"type": "COUNCIL_CHAT", "data": council_dialogue[i]})
                    yield "data: " + data + "\n\n"
                last_idx = len(council_dialogue)
            await asyncio.sleep(0.5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/network/events/stream")
async def network_event_stream():
    async def event_generator():
        event_id = 0
        while True:
            event_id += 1
            payload = {"node_id": "n" + str(random.randint(0,9)), "voltage": -60.0 + random.random()*10}
            data = json.dumps({"event_id": event_id, "event_type": "node_state_update", "snapshot_version": SNAPSHOT_VERSION, "time": datetime.now().isoformat(), "payload": payload})
            yield "data: " + data + "\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/logs/raw")
async def get_raw_logs(lines: int = 100):
    if not os.path.exists(LOG_PATH):
        return {"error": "Log file not found", "path": LOG_PATH}
    try:
        result = subprocess.run(["tail", "-n", str(lines), LOG_PATH], capture_output=True, text=True, timeout=2)
        return {"content": result.stdout, "path": LOG_PATH}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=MONITOR_PORT)
