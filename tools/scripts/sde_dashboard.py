import os
import asyncio
import json
import logging
import random
import re
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Import the core engine (adjusted path for the new structure)
import sys
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

try:
    from gamma_runtime.app import server, current_bridge_type, remote_host, init_server
except ImportError:
    # Fallback for standalone testing
    server = None
    current_bridge_type = "mock"
    remote_host = "100.64.0.2"
    def init_server(*args, **kwargs): pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Omission_Dashboard")

app = FastAPI()

# Mount the outputs directory for artifact rendering
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=str(OUTPUTS_DIR)), name="artifacts")

subscribers = []

def broadcast(data):
    for q in subscribers:
        q.put_nowait(json.dumps(data))

def get_discovered_artifacts():
    """Scans outputs/ for directories containing index.html"""
    artifacts = []
    if not OUTPUTS_DIR.exists():
        return []
    for item in OUTPUTS_DIR.iterdir():
        if item.is_dir() and (item / "index.html").exists():
            meta_path = item / "meta.json"
            meta = {}
            if meta_path.exists():
                try:
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                except:
                    pass
            
            artifacts.append({
                "id": item.name,
                "title": meta.get("title", item.name.replace("_", " ").title()),
                "path": f"/artifacts/{item.name}/index.html",
                "timestamp": os.path.getmtime(item / "index.html")
            })
    return sorted(artifacts, key=lambda x: x["timestamp"], reverse=True)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    artifacts = get_discovered_artifacts()
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Omission | Arena Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            :root {{
                --bg: #0a0a0a;
                --panel: #141414;
                --border: #333;
                --text: #f0f0f0;
                --text-dim: #888;
                --accent: #CFB87C;
                --error: #ff4444;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                background: var(--bg);
                color: var(--text);
                font-family: 'Inter', sans-serif;
                display: grid;
                grid-template-columns: 280px 1fr 350px;
                grid-template-rows: 60px 1fr 200px;
                height: 100vh;
                overflow: hidden;
            }}
            
            /* Sidebar / Gallery */
            .sidebar {{
                grid-row: 1 / 4;
                background: var(--panel);
                border-right: 1px solid var(--border);
                display: flex;
                flex-direction: column;
                padding: 20px;
            }}
            .brand {{ font-weight: 700; letter-spacing: 2px; color: var(--accent); margin-bottom: 30px; }}
            .artifact-list {{ flex-grow: 1; overflow-y: auto; }}
            .artifact-item {{
                padding: 12px;
                margin-bottom: 8px;
                border: 1px solid var(--border);
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 0.85em;
            }}
            .artifact-item:hover {{ border-color: var(--accent); background: rgba(207, 184, 124, 0.05); }}
            .artifact-item.active {{ background: var(--accent); color: #000; border-color: var(--accent); }}

            /* Top Bar */
            .header {{
                grid-column: 2 / 4;
                background: var(--panel);
                border-bottom: 1px solid var(--border);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 20px;
                font-family: 'JetBrains Mono', monospace;
            }}

            /* Viewer Area */
            .viewer {{
                grid-column: 2 / 3;
                background: #000;
                position: relative;
            }}
            iframe {{ width: 100%; height: 100%; border: none; }}

            /* Live Metrics Area */
            .inspector {{
                grid-column: 3 / 4;
                background: var(--panel);
                border-left: 1px solid var(--border);
                padding: 20px;
                display: flex;
                flex-direction: column;
            }}

            /* Bottom Panel */
            .console {{
                grid-column: 2 / 4;
                background: var(--panel);
                border-top: 1px solid var(--border);
                padding: 15px;
                overflow-y: auto;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85em;
            }}

            .btn {{
                background: transparent;
                border: 1px solid var(--accent);
                color: var(--accent);
                padding: 6px 12px;
                cursor: pointer;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8em;
            }}
            .btn:hover {{ background: var(--accent); color: #000; }}
            
            .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }}
            .metric-card {{ background: #1a1a1a; padding: 10px; border-radius: 4px; }}
            .m-label {{ font-size: 0.7em; color: var(--text-dim); }}
            .m-value {{ font-size: 1.2em; font-weight: 700; color: var(--accent); }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand">OMISSION ARENA</div>
            <div class="section-label" style="font-size: 0.7em; color: var(--text-dim); margin-bottom: 10px;">ARTIFACTS</div>
            <div class="artifact-list" id="artifact-list">
                {"".join([f'<div class="artifact-item" onclick="loadArtifact(\'{a["path"]}\', this)">{a["title"]}</div>' for a in artifacts])}
            </div>
        </div>

        <header class="header">
            <div>
                [STATUS] <span id="status" style="color: var(--accent)">LISTENING</span> | BRIDGE: {current_bridge_type.upper()}
            </div>
            <div class="controls">
                <button class="btn" onclick="fetch('/step')">STEP</button>
                <button class="btn" onclick="toggleAuto()" id="auto-btn">AUTO</button>
                <button class="btn" onclick="fetch('/reset')" style="border-color: var(--error); color: var(--error);">RESET</button>
            </div>
        </header>

        <div class="viewer">
            <iframe id="artifact-frame" src="about:blank"></iframe>
        </div>

        <div class="inspector">
            <div class="tag" style="color: var(--accent); font-weight: bold; margin-bottom: 15px;">LIVE METRICS</div>
            <div id="state-plot" style="height: 200px;"></div>
            <div class="metrics-grid">
                <div class="metric-card"><div class="m-label">X</div><div class="m-value" id="m-x">0.00</div></div>
                <div class="metric-card"><div class="m-label">Y</div><div class="m-value" id="m-y">0.00</div></div>
                <div class="metric-card"><div class="m-label">Z</div><div class="m-value" id="m-z">0.00</div></div>
                <div class="metric-card"><div class="m-label">W</div><div class="m-value" id="m-w">0.00</div></div>
            </div>
        </div>

        <div class="console" id="log-content">
            <div style="color: var(--text-dim)">Console initialized. Waiting for trace...</div>
        </div>

        <script>
            function loadArtifact(path, el) {{
                document.getElementById('artifact-frame').src = path;
                document.querySelectorAll('.artifact-item').forEach(i => i.classList.remove('active'));
                el.classList.add('active');
            }}

            let plotData = {{ x: [], y: [], z: [], w: [], epochs: [] }};
            function updatePlot() {{
                const traces = [
                    {{ x: plotData.epochs, y: plotData.x, name: 'X', line: {{color: '#CFB87C', width: 2}} }},
                    {{ x: plotData.epochs, y: plotData.y, name: 'Y', line: {{color: '#9400D3', width: 2}} }},
                    {{ x: plotData.epochs, y: plotData.z, name: 'Z', line: {{color: '#00FF00', width: 2}} }},
                    {{ x: plotData.epochs, y: plotData.w, name: 'W', line: {{color: '#00FFFF', width: 2}} }}
                ];
                const layout = {{
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{ color: '#f0f0f0', family: 'JetBrains Mono', size: 10 }},
                    margin: {{ t: 10, b: 20, l: 30, r: 10 }},
                    xaxis: {{ gridcolor: '#222' }},
                    yaxis: {{ gridcolor: '#222', range: [0, 1.1] }},
                    showlegend: false
                }};
                Plotly.newPlot('state-plot', traces, layout);
            }}

            const evtSource = new EventSource("/stream");
            evtSource.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                if (data.type === "turn") {{
                    const res = data.result;
                    plotData.epochs.push(res.epoch);
                    plotData.x.push(res.x); plotData.y.push(res.y);
                    plotData.z.push(res.z); plotData.w.push(res.w);
                    updatePlot();

                    document.getElementById('m-x').innerText = res.x.toFixed(3);
                    document.getElementById('m-y').innerText = res.y.toFixed(3);
                    document.getElementById('m-z').innerText = res.z.toFixed(3);
                    document.getElementById('m-w').innerText = res.w.toFixed(3);
                    document.getElementById('status').innerText = "EPOCH " + res.epoch;

                    const logContent = document.getElementById('log-content');
                    res.proposals.forEach(p => {{
                        const div = document.createElement('div');
                        div.style.marginBottom = "5px";
                        div.innerHTML = `<span style="color: var(--accent)">[${{p.player_id}}]</span> ${{p.raw_text}}`;
                        logContent.prepend(div);
                    }});
                }}
            }};

            let autoMode = false;
            async function toggleAuto() {{
                autoMode = !autoMode;
                document.getElementById('auto-btn').innerText = autoMode ? "STOP" : "AUTO";
                while (autoMode) {{
                    await fetch('/step');
                    await new Promise(r => setTimeout(r, 2000));
                }}
            }}
            updatePlot();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/stream")
async def message_stream(request: Request):
    async def event_generator():
        q = asyncio.Queue()
        subscribers.append(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield {"data": data}
        finally:
            subscribers.remove(q)

    return EventSourceResponse(event_generator())

@app.get("/step")
async def step_game():
    if server:
        result = await server.run_epoch()
        broadcast({"type": "turn", "result": result.to_dict()})
        return {"status": "ok", "epoch": result.epoch}
    return {"status": "error", "message": "Server not initialized"}

@app.get("/reset")
async def reset_game():
    if init_server:
        init_server("dummy", "mock")
        broadcast({"type": "reset"})
        return {"status": "reset"}
    return {"status": "error", "message": "Server not initialized"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3005)
