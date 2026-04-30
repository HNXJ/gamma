import os
import sqlite3
import json
import time
import re
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import plotly.graph_objects as go

from fastapi.staticfiles import StaticFiles

app = FastAPI()

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
                                council_dialogue.append({"time": ts, "agent": agent, "msg": msg})
                                if len(council_dialogue) > 50: council_dialogue.pop(0)
                                tps_stats["total_tokens"] += len(msg.split()) * 4 # Approximation
                        
                        # Simple TPS calc
                        now = time.time()
                        if now - tps_stats["last_tps_check"] > 5:
                            tps_stats["tps"] = (len(lines) * 5) / 5 # Simplified
                            tps_stats["last_tps_check"] = now
        except Exception as e:
            pass # Keep monitor quiet during path discovery
        time.sleep(1)

# Start background thread
import threading
if LOG_PATH != "/dev/null":
    threading.Thread(target=update_monitor_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="arena.html")

@app.get("/council", response_class=HTMLResponse)
async def council(request: Request):
    return templates.TemplateResponse(request=request, name="arena.html")

@app.get("/guard", response_class=HTMLResponse)
async def guard(request: Request):
    return templates.TemplateResponse(request=request, name="guard.html")

@app.get("/api/status")
async def get_status():
    """
    Grounded Status for the Amber Arena.
    Sources progression state from arena_patch_board.json.
    """
    latest_msg = council_dialogue[-1] if council_dialogue else {}
    
    # Load progression board
    progression = {}
    board_path = os.path.join(ROOT_DIR, "context/configs/patches/arena_patch_board.json")
    if os.path.exists(board_path):
        try:
            with open(board_path, "r") as f:
                progression = json.load(f)
        except Exception as e:
            print(f"Progression load error: {e}")

    # Grounded metrics from user and live logs
    active_slots = 3
    total_slots = 4
    
    # Load NAMESPACED Arena World State (The Truth Source)
    world_state = { 
        "boot_type": "UNKNOWN", 
        "resume_count": 0, 
        "freshness": "DEGRADED",
        "official_level_metric": "largest_pass_network_neuron_count",
        "largest_pass_network_neuron_count": 10,
        "accepted_streak": 0
    }
    world_path = os.path.join(ROOT_DIR, "local/game001/arena_runtime_state.json")
    if os.path.exists(world_path):
        try:
            with open(world_path, "r") as f:
                ckpt = json.load(f)
                world_state.update(ckpt)
                world_state["boot_type"] = "RESUMED" if len(ckpt.get("boot_history", [])) > 1 else "FRESH"
                world_state["resume_count"] = len(ckpt.get("boot_history", [])) - 1
                last_ts_str = ckpt.get("last_checkpoint_time")
                if last_ts_str:
                    last_dt = datetime.fromisoformat(last_ts_str)
                    world_state["last_checkpoint"] = last_dt.strftime("%H:%M:%S")
                    world_state["freshness"] = "GROUNDED" if (datetime.now() - last_dt).total_seconds() < 600 else "STALE"
                else:
                    world_state["last_checkpoint"] = "NEVER"
        except Exception as e:
            print(f"World state load error: {e}")

    return {
        "system": {
            "status": "ONLINE" if council_dialogue else "STANDBY",
            "uptime": "00:00:00",
            "backend_active_slots": f"{active_slots} / {total_slots}",
            "tasks_running": 0,
            "heartbeat": "OK" if council_dialogue else "STALLED"
        },
        "progression": progression,
        "persistence": {
            "boot_type": world_state["boot_type"],
            "resume_count": world_state["resume_count"],
            "last_checkpoint": world_state.get("last_checkpoint", "NEVER"),
            "freshness": world_state["freshness"]
        },
        "research": {
            "neuron_count": world_state.get("largest_pass_network_neuron_count"),
            "pass_network": f"{world_state.get('largest_pass_network_neuron_count')}-Node Grounded",
            "active_patch": world_state.get("active_patches", ["v1.1.0"])[0],
            "omissions": world_state.get("omissions", 0),
            "accepted_streak": world_state.get("accepted_streak", 0)
        },
        "sessions": [
            {
                "id": "G01",
                "role": "Monitor",
                "status": "ACTIVE" if council_dialogue else "IDLE",
                "last_active": latest_msg.get("time", ""),
                "truth_class": "GROUNDED",
                "source": LOG_PATH
            },
            { "id": "G02", "role": "Optimizer", "status": "IDLE", "last_active": "", "truth_class": "DEGRADED", "source": "null" },
            { "id": "G03", "role": "Analyst", "status": "IDLE", "last_active": "", "truth_class": "DEGRADED", "source": "null" },
            { "id": "G04", "role": "Manager", "status": "IDLE", "last_active": "", "truth_class": "DEGRADED", "source": "null" }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3012)
