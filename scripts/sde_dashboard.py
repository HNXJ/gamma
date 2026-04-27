#!/usr/bin/env python3
"""
SDE Game Dashboard: Interactive FastAPI viewer for the SDE Game Server.
Provides a real-time dashboard for Antigravity (M1-Max).
"""

import asyncio
import json
import logging
import random
import re
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

# Import the core engine
from sde_game_server import (
    SDEGameServer, PlayerAgent, MockExecutionBridge, SSHExecutionBridge,
    PlayerProposal, DummyMathPolicy, HypothesisGenerationPolicy, MethodSelectionPolicy,
    EmergentScientificDebatePolicy, TurnResult, GameState
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SDE_Dashboard")

app = FastAPI()

# ==========================================
# 1. GLOBAL ENGINE STATE
# ==========================================

server = None
current_bridge_type = "mock"
lm_studio_url = os.environ.get("LMSTUDIO_URL", "http://localhost:1234")
remote_host = os.environ.get("REMOTE_HOST", "100.64.0.2")

async def dynamic_agent_proposal(agent, prompt):
    policy_name = server.policy.name if server.policy else ""
    
    # If using real LM Studio (local or remote), use the agent's real method
    if current_bridge_type == "ssh" or os.environ.get("FORCE_REAL_LLM"):
         return await agent.get_proposal(prompt)
    
    # Otherwise, fallback to mock logic for local testing/demo
    await asyncio.sleep(0.3)
    if "Dummy" in policy_name:
        epoch_match = re.search(r'Epoch: (\d+)', prompt)
        epoch = int(epoch_match.group(1)) if epoch_match else 1
        val = min(60, 40 + epoch * 5 + random.randint(-2, 2)) if agent.agent_id == "G1" else 40
        return PlayerProposal(agent.agent_id, agent.role, f"I propose {val}", {"value": val}, True)
    
    elif "Hypothesis" in policy_name:
        choices = [
            "The Inhibition-Stabilized Network is mediated by SST cells.",
            "Gamma-Oscillation Decay suggests a breakdown in PV-mediated gain.",
            "Our model shows stable ISN dynamics under varying AMPA conductance."
        ]
        text = random.choice(choices)
        return PlayerProposal(agent.agent_id, agent.role, text, {}, True)
    
    elif "Method" in policy_name:
        choices = ["Patch-clamp", "Optogenetics", "CSD analysis"]
        m1, m2 = random.sample(choices, 2)
        return PlayerProposal(agent.agent_id, agent.role, f"Methods: {m1} and {m2}", {}, True)

    elif "Debate" in policy_name:
        choices = [
            "I propose AMPA=12nS, GABA=5ms, and mu=0.5 based on the source.",
            "I AGREE with G1's assessment of the peak conductance.",
            "Wait, I see GABA is 5ms, but G1 didn't specify the weight distribution. I propose mu=0.5.",
            "I AGREE. The final parameters should be [12, 5, 0.5]."
        ]
        text = random.choice(choices)
        return PlayerProposal(agent.agent_id, agent.role, text, {}, True)
    
    return PlayerProposal(agent.agent_id, agent.role, "Default response", {}, True)

def init_server(policy_type="dummy", bridge_type="mock", lm_url=None, model_key=None):
    global server, current_bridge_type, lm_studio_url
    
    current_bridge_type = bridge_type
    if lm_url:
        lm_studio_url = lm_url
    
    m_key = model_key or os.environ.get("LM_MODEL_KEY", "gemma4-parallel")

    bridge = SSHExecutionBridge(hostname=remote_host) if bridge_type == "ssh" else MockExecutionBridge()
    server = SDEGameServer(bridge)
    
    if policy_type == "hypothesis":
        server.load_policy(HypothesisGenerationPolicy())
    elif policy_type == "method":
        server.load_policy(MethodSelectionPolicy())
    elif policy_type == "debate":
        server.load_policy(EmergentScientificDebatePolicy())
    else:
        server.load_policy(DummyMathPolicy())
    
    # 3-Agent Setup for Debate, 2-Agent for others
    agent_ids = ["G1", "G2", "G3"] if policy_type == "debate" else ["G1", "G2"]
    
    for aid in agent_ids:
        role = "Architect"
        player = PlayerAgent(aid, role, lm_studio_url, model_name=m_key)
        
        if bridge_type == "mock" and not os.environ.get("FORCE_REAL_LLM"):
            player.get_proposal = lambda p, a=player: dynamic_agent_proposal(a, p)
        
        server.add_player(player)

# Initial default
init_server("dummy", "mock")

# SSE Stream Queue
subscribers = []

def broadcast(data: dict):
    payload = json.dumps(data)
    for q in subscribers:
        q.put_nowait(payload)

# ==========================================
# 2. API ENDPOINTS
# ==========================================

@app.get("/")
async def get_dashboard():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>SDE Game Server Monitor</title>
        <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #0a0a0b;
                --surface: rgba(20, 20, 22, 0.7);
                --border: #CFB87C;
                --accent: #9400D3;
                --text: #f0f0f0;
                --mono: 'JetBrains Mono', monospace;
            }}
            body {{
                background: var(--bg);
                color: var(--text);
                font-family: var(--mono);
                margin: 0;
                padding: 10px;
                display: grid;
                grid-template-columns: 2fr 1fr;
                grid-template-rows: 80px 1fr 200px;
                height: 100vh;
                gap: 10px;
                box-sizing: border-box;
            }}
            .panel {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 4px;
                padding: 15px;
                overflow-y: auto;
            }}
            .header {{
                grid-column: 1 / span 2;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 20px;
            }}
            .controls button, .controls select, .controls input {{
                background: transparent;
                border: 1px solid var(--border);
                color: var(--border);
                padding: 5px 10px;
                cursor: pointer;
                font-family: var(--mono);
                margin-left: 5px;
            }}
            .controls input {{ cursor: text; width: 150px; color: #fff; }}
            .controls button:hover {{
                background: var(--border);
                color: var(--bg);
            }}
            .plot-container {{
                grid-row: 2;
            }}
            .log-panel {{
                grid-row: 2 / span 2;
                grid-column: 2;
                font-size: 12px;
            }}
            .metrics-grid {{
                grid-row: 3;
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
            }}
            .metric-card {{
                text-align: center;
                padding: 10px;
                border-bottom: 2px solid var(--accent);
            }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: var(--border); }}
            .metric-label {{ font-size: 10px; color: var(--text-dim); }}
            
            .agent-block {{
                margin-bottom: 10px;
                padding: 8px;
                border-left: 3px solid var(--accent);
                background: rgba(255,255,255,0.05);
            }}
            .tag {{ font-weight: bold; color: var(--border); }}
        </style>
    </head>
    <body>
        <div class="panel header">
            <div>
                [GAMMA] SDE SERVER - <span id="status" style="color: var(--accent)">READY</span><br>
                <small style="color: #888">Bridge: <span id="bridge-info">{current_bridge_type.upper()}</span> | Host: {remote_host}</small>
            </div>
            <div class="controls">
                <input type="text" id="lm-url" value="{lm_studio_url}" placeholder="LM Studio URL">
                <input type="text" id="model-key" value="gemma4-parallel" placeholder="Model Key">
                <select id="bridge-select">
                    <option value="mock">MOCK BRIDGE</option>
                    <option value="ssh">SSH CLUSTER</option>
                </select>
                <select id="policy-select">
                    <option value="dummy">Math Convergence</option>
                    <option value="hypothesis">Hypothesis Generation</option>
                    <option value="method">Method Selection</option>
                    <option value="debate">Scientific Debate (Emergent)</option>
                </select>
                <button onclick="initPolicy()">INIT</button>
                <button onclick="fetch('/step')">NEXT</button>
                <button id="auto-btn" onclick="toggleAuto()">AUTO</button>
                <button onclick="fetch('/reset')" style="border-color: #ff4444; color: #ff4444">RESET</button>
            </div>
        </div>

        <div class="panel plot-container" id="state-plot"></div>

        <div class="panel log-panel" id="logs">
            <div class="tag">System Log</div>
            <div id="log-content" style="margin-top: 10px"></div>
        </div>

        <div class="panel metrics-grid">
            <div class="metric-card"><div class="metric-label">X (Convergence)</div><div class="metric-value" id="m-x">0.00</div></div>
            <div class="metric-card"><div class="metric-label">Y (Rigor)</div><div class="metric-value" id="m-y">0.00</div></div>
            <div class="metric-card"><div class="metric-label">Z (Bio Truth)</div><div class="metric-value" id="m-z">0.00</div></div>
            <div class="metric-card"><div class="metric-label">W (Consensus)</div><div class="metric-value" id="m-w">0.00</div></div>
        </div>

        <script>
            let plotData = {{ x: [], y: [], z: [], w: [], epochs: [] }};

            function initPolicy() {{
                const p = document.getElementById('policy-select').value;
                const b = document.getElementById('bridge-select').value;
                const url = document.getElementById('lm-url').value;
                const m = document.getElementById('model-key').value;
                
                fetch(`/init_policy?type=${{p}}&bridge=${{b}}&lm_url=${{encodeURIComponent(url)}}&model_key=${{encodeURIComponent(m)}}`).then(() => {{
                    plotData = {{ x: [], y: [], z: [], w: [], epochs: [] }};
                    updatePlot();
                    document.getElementById('log-content').innerHTML = "<em>Initialized: " + p + " / " + b + "</em>";
                    document.getElementById('bridge-info').innerText = b.toUpperCase();
                }});
            }}

            function updatePlot() {{
                const traces = [
                    {{ x: plotData.epochs, y: plotData.x, name: 'X', line: {{color: '#CFB87C'}} }},
                    {{ x: plotData.epochs, y: plotData.y, name: 'Y', line: {{color: '#9400D3'}} }},
                    {{ x: plotData.epochs, y: plotData.z, name: 'Z', line: {{color: '#00FF00'}} }},
                    {{ x: plotData.epochs, y: plotData.w, name: 'W', line: {{color: '#00FFFF'}} }}
                ];
                const layout = {{
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{ color: '#f0f0f0', family: 'JetBrains Mono' }},
                    margin: {{ t: 40, b: 40, l: 40, r: 40 }},
                    xaxis: {{ gridcolor: '#333', title: 'Epoch' }},
                    yaxis: {{ gridcolor: '#333', range: [0, 1.2] }}
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
                        div.className = 'agent-block';
                        div.innerHTML = `<span class="tag">${{p.player_id}}:</span> ${{p.raw_text}}<br>
                                         <small style="color: #f0f0f088">FEEDBACK: ${{res.feedback_by_player[p.player_id]}}</small>`;
                        logContent.prepend(div);
                    }});
                }} else if (data.type === "reset") {{
                    plotData = {{ x: [], y: [], z: [], w: [], epochs: [] }};
                    updatePlot();
                    document.getElementById('log-content').innerHTML = "<em>Engine Reset.</em>";
                }}
            }};

            let autoMode = false;
            async function toggleAuto() {{
                autoMode = !autoMode;
                document.getElementById('auto-btn').innerText = autoMode ? "STOP" : "AUTO";
                while (autoMode) {{
                    const r = await fetch('/step');
                    const d = await r.json();
                    if (d.epoch > 50) break; 
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

@app.get("/init_policy")
async def api_init_policy(type: str = "dummy", bridge: str = "mock", lm_url: str = None, model_key: str = "gemma4-parallel"):
    init_server(type, bridge, lm_url, model_key)
    broadcast({"type": "reset"})
    return {"status": "initialized", "policy": type, "bridge": bridge}

@app.get("/step")
async def step_game():
    result = await server.run_epoch()
    broadcast({"type": "turn", "result": result.to_dict()})
    return {"status": "ok", "epoch": result.epoch}

@app.get("/reset")
async def reset_game():
    init_server("dummy", "mock")
    broadcast({"type": "reset"})
    return {"status": "reset"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3005)
