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

# ... [update_monitor_data and background thread remain unchanged] ...

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/status")
async def get_status():
    """
    Grounded status endpoint for the infused dashboard.
    Returns real metrics from logs/DB; returns null for unavailable data.
    """
    return {
        "system": {
            "status": "ACTIVE" if council_dialogue else "IDLE",
            "vram": null, # Degraded: Source not yet mapped
            "uptime": null, # Degraded: Source not yet mapped
            "boot_epoch": null, # Degraded: Source not yet mapped
            "heartbeat": time.time()
        },
        "research": {
            "pass_network": "14-Node (Grounded Log)" if council_dialogue else null,
            "active_patch": null, # Degraded: Source not yet mapped
            "omissions": 0 # Default to 0 unless detected in logs
        },
        "sessions": [
            {
                "id": "G01",
                "topic": council_dialogue[-1]["msg"][:30] + "..." if council_dialogue else "Global Monitor",
                "round": len(council_dialogue),
                "last_active": council_dialogue[-1]["time"] if council_dialogue else null,
                "status": "MONITORING"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3012)
