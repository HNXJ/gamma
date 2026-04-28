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

app = FastAPI()

# Paths relative to the script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
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
    # Physics Manifold
    df = pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH, uri=True)
        query = "SELECT x, y, z, w, total_loss, timestamp, 'e4b' as agent FROM manifold ORDER BY timestamp DESC LIMIT 20"
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception as e:
        print(f"Ledger read error: {e}")

    # Layout
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df['x'], y=df['z'], mode='markers', marker=dict(size=10, color=df['total_loss'])))
    
    fig.update_layout(plot_bgcolor="#0D0D0D", paper_bgcolor="#0D0D0D", font_color="#CFB87C", margin=dict(l=20, r=20, t=30, b=20))
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return templates.TemplateResponse(
        request=request, 
        name="monitor.html", 
        context={
            "dialogue": council_dialogue[-20:],
            "tps": tps_stats["tps"],
            "total_tokens": tps_stats["total_tokens"],
            "graph_html": graph_html,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3012)
