import os
import sqlite3
import json
import time
import re
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import plotly.graph_objects as go
import subprocess
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles

app = FastAPI()
APP_START_TIME = datetime.now(timezone.utc)

# Dynamic Path Resolution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "dashboard", "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "dashboard", "static")

# Explicit Static Mounting
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Environment-based paths for logs and DB
DB_PATH = os.getenv("GAMMA_DB_PATH", "file::memory:?cache=shared")
LOG_PATH = os.getenv("GAMMA_LOG_PATH", "/dev/null")

# Global state for streaming logs
council_dialogue = []
tps_stats = {"total_tokens": 0, "last_tps_check": time.time(), "tps": 0.0}

def update_monitor_data():
    global council_dialogue, tps_stats
    last_pos = 0
    while True:
        try:
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "r") as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    last_pos = f.tell()
                    
                    for line in lines:
                        # Regex Extraction: [Agent], [Timestamp], [Message]
                        match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - INFO - (.*)", line)
                        if match:
                            ts, agent, msg = match.groups()
                            if any(a in agent for a in ["Macro", "Meso", "Micro", "Critic"]):
                                entry = {"time": ts, "agent": agent, "msg": msg}
                                council_dialogue.append(entry)
                                if len(council_dialogue) > 50: council_dialogue.pop(0)
                                tps_stats["total_tokens"] += len(msg.split()) * 4 # Approximation
                        
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

@app.get("/api/status")
async def get_status():
    """
    Grounded Snapshot for the Amber Arena (Phase 1.6 Frozen).
    Explicitly splits Backend Slots from Grounded Agents.
    """
    progression = await get_progression()
    persistence = await get_persistence()
    health = await get_health()
    
    return {
        "system": {
            "status": "ONLINE" if council_dialogue else "STANDBY",
            "uptime": health["uptime"],
            "backend_active_slots": "3 / 4",
            "heartbeat": health["heartbeat"]
        },
        "progression": progression,
        "persistence": persistence,
        "research": {
            "neuron_count": progression.get("largest_pass_network_neuron_count"),
            "pass_network": f"{progression.get('largest_pass_network_neuron_count')}-Node Grounded",
            "active_patch": progression.get("active_patches", ["v1.1.0"])[0] if progression.get("active_patches") else "v1.1.0",
            "omissions": progression.get("omissions", 0),
            "grounded_agents_active": sum(1 for s in (await get_agents()) if s["status"] == "ACTIVE")
        }
    }

@app.get("/api/progression")
async def get_progression():
    """
    Authoritative scientific progression grounded in both manifest and runtime state.
    """
    # 1. Base from Patch Board
    state = {"largest_pass_network_neuron_count": 10, "active_patches": [], "truth_class": "INFERRED"}
    board_path = os.path.join(ROOT_DIR, "context/configs/patches/arena_patch_board.json")
    if os.path.exists(board_path):
        try:
            with open(board_path, "r") as f:
                state.update(json.load(f))
        except Exception: pass
    
    # 2. Ground with Namespaced World State (The Live Truth)
    world_path = os.path.join(ROOT_DIR, "local/game001/arena_runtime_state.json")
    if os.path.exists(world_path):
        try:
            with open(world_path, "r") as f:
                world = json.load(f)
                state["largest_pass_network_neuron_count"] = world.get("largest_pass_network_neuron_count", state["largest_pass_network_neuron_count"])
                state["truth_class"] = "GROUNDED"
        except Exception: pass
        
    return state

@app.get("/api/agents")
async def get_agents():
    """
    Grounded agent activity and evidence.
    """
    latest_msg = council_dialogue[-1] if council_dialogue else {}
    return [
        {
            "id": "G01",
            "role": "Monitor",
            "status": "ACTIVE" if council_dialogue else "IDLE",
            "last_active": latest_msg.get("time", ""),
            "truth_class": "GROUNDED",
            "source": LOG_PATH
        },
        { "id": "G02", "role": "Optimizer", "status": "IDLE", "last_active": "", "truth_class": "DEGRADED", "source": None },
        { "id": "G03", "role": "Analyst", "status": "IDLE", "last_active": "", "truth_class": "DEGRADED", "source": None },
        { "id": "G04", "role": "Manager", "status": "IDLE", "last_active": "", "truth_class": "DEGRADED", "source": None }
    ]

@app.get("/api/persistence")
async def get_persistence():
    """
    Metadata from the canonical namespaced runtime state.
    """
    persistence = { "boot_type": "UNKNOWN", "freshness": "DEGRADED", "resume_count": 0 }
    runtime_path = os.path.join(ROOT_DIR, "local/game001/arena_runtime_state.json")
    if os.path.exists(runtime_path):
        try:
            with open(runtime_path, "r") as f:
                ckpt = json.load(f)
                persistence["boot_type"] = "RESUMED" if len(ckpt.get("boot_history", [])) > 1 else "FRESH"
                persistence["resume_count"] = len(ckpt.get("boot_history", [])) - 1
                last_ts_str = ckpt.get("last_checkpoint_time")
                if last_ts_str:
                    last_dt = datetime.fromisoformat(last_ts_str)
                    persistence["last_checkpoint"] = last_dt.strftime("%H:%M:%S")
                    persistence["freshness"] = "GROUNDED" if (datetime.now() - last_dt).total_seconds() < 600 else "STALE"
        except Exception:
            pass
    return persistence

@app.get("/api/health")
async def get_health():
    """
    Grounded health and uptime metrics.
    """
    now = datetime.now(timezone.utc)
    delta = now - APP_START_TIME
    uptime_str = str(delta).split(".")[0] # HH:MM:SS
    
    return {
        "status": "OK",
        "uptime": uptime_str,
        "heartbeat": "OK" if council_dialogue else "STALLED",
        "last_signal": council_dialogue[-1].get("time") if council_dialogue else None
    }

@app.get("/api/events/stream")
async def event_stream(request: Request):
    """
    Real-time event stream (SSE) for the Arena timeline.
    """
    async def event_generator():
        last_sent_idx = len(council_dialogue)
        while True:
            if await request.is_disconnected():
                break
            
            if len(council_dialogue) > last_sent_idx:
                for i in range(last_sent_idx, len(council_dialogue)):
                    yield f"data: {json.dumps(council_dialogue[i])}\n\n"
                last_sent_idx = len(council_dialogue)
            
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/logs/raw")
async def get_raw_logs(lines: int = 100):
    """
    Raw tail of the orchestrator log for debugging proof.
    """
    if not os.path.exists(LOG_PATH):
        return {"error": "Log file not found", "path": LOG_PATH}
    
    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), LOG_PATH],
            capture_output=True,
            text=True,
            timeout=2
        )
        return {"content": result.stdout, "path": LOG_PATH}
    except Exception as e:
        return {"error": str(e)}

# POST /api/terminal/exec is removed from migration scope (Phase 1.6)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3012)
