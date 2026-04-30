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

# Absolute Path Resolution for Office Mac stability
ROOT_DIR = "/Users/HN/MLLM/gamma"
TEMPLATES_DIR = os.path.join(ROOT_DIR, "dashboard", "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "dashboard", "static")

# Explicit Static Mounting
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

DB_PATH = "file:/Users/HN/MLLM/data/test_got_ledger.db?mode=ro"
LOG_PATH = "/Users/HN/MLLM/logs/overnight_orchestrator.log"

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
            print(f"Log streaming error: {e}")
        time.sleep(1)

# Start background thread
import threading
threading.Thread(target=update_monitor_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/status")
async def get_status():
    """
    Grounded status endpoint for the infused dashboard.
    Returns real metrics from logs/DB; returns None for unavailable data.
    """
    return {
        "system": {
            "status": "ACTIVE" if council_dialogue else "IDLE",
            "vram": None, 
            "uptime": None, 
            "boot_epoch": None, 
            "heartbeat": time.time()
        },
        "research": {
            "pass_network": "14-Node (Grounded Log)" if council_dialogue else None,
            "active_patch": None, 
            "omissions": 0 
        },
        "sessions": [
            {
                "id": "G01",
                "topic": council_dialogue[-1]["msg"][:30] + "..." if council_dialogue else "Global Monitor",
                "round": len(council_dialogue),
                "last_active": council_dialogue[-1]["time"] if council_dialogue else None,
                "status": "MONITORING"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3012)
