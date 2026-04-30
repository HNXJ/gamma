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

    # Persistence metadata from the canonical namespaced runtime state
    persistence = { "boot_type": "UNKNOWN", "freshness": "DEGRADED", "resume_count": 0 }
    runtime_path = os.path.join(ROOT_DIR, "local/game001/arena_runtime_state.json")
    if os.path.exists(runtime_path):
        try:
            with open(runtime_path, "r") as f:
                ckpt = json.load(f)
                persistence["boot_type"] = "RESUMED" if ckpt.get("resume_count", 0) > 0 else "FRESH"
                persistence["resume_count"] = ckpt.get("resume_count", 0)
                last_ts = ckpt.get("last_checkpoint_time", 0)
                persistence["last_checkpoint"] = datetime.fromtimestamp(last_ts).isoformat() if last_ts else "NEVER"
                persistence["freshness"] = "GROUNDED" if (time.time() - last_ts < 300) else "STALE"
        except Exception as e:
            print(f"Runtime state load error: {e}")
    
    # Authoritative Truth Resolution
    largest_pass = progression.get("largest_pass_network_neuron_count")
    active_patches = progression.get("active_patches", [])
    
    return {
        "system": {
            "status": "ONLINE" if council_dialogue else "STANDBY",
            "uptime": None,
            "agents_active": None,
            "tasks_running": None,
            "heartbeat": "OK" if council_dialogue else "STALLED"
        },
        "progression": progression,
        "persistence": persistence,
        "research": {
            "neuron_count": largest_pass,
            "pass_network": f"{largest_pass}-Node Grounded" if largest_pass else None,
            "active_patch": active_patches[0] if active_patches else None,
            "omissions": progression.get("omissions")
        },
        "sessions": progression.get("sessions", [])
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3012)
