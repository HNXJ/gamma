#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "asyncio",
#     "fastapi",
#     "uvicorn",
#     "sse-starlette",
#     "jax",
#     "jaxlib",
#     "jaxley"
# ]
# ///

import asyncio
import httpx
import json
import time
import re
import sys
import jax
import jax.numpy as jnp
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn
import jaxley as jx
from jaxley.channels import Leak
from jaxley.synapses import Ionotropic

app = FastAPI()

LMSTUDIO_BASE_URL = "http://127.0.0.1:1234"
TARGET_MODEL = "gemma-4-e4b-it-mxfp8"

state = {
    "epoch": 0,
    "z": 1.0,         # G1 bio-plausibility 
    "w": 1.0,         # G2 bio-plausibility 
    "x": 0.0,         # Epistemic Gain (MSE reduction)
    "y": 0.0,         # System Throughput
    "loss": 0.0,      # Equilibrium Loss
    "logs": ["[System] Booting Jaxley SDE FedLoRA Aggregate Node..."],
    "status": "Initializing Engine"
}

subscribers = []

def log(msg: str):
    print(msg)
    state["logs"].append(msg)
    if len(state["logs"]) > 50:
        state["logs"].pop(0)
    broadcast_state()

def broadcast_state():
    for sub in subscribers:
        sub.put_nowait(json.dumps(state))

# ==========================================
# BIOPHYSICAL ENVIRONMENT
# ==========================================

# Base Network
class BasicCell(jx.Module):
    def __init__(self):
        super().__init__()
        self.soma = jx.Compartment()
        self.soma.insert(Leak())

def run_simulation(gaba_gmax, ampa_gmax):
    try:
        # Build cell
        cell = BasicCell()
        net = jx.Network([cell, cell])
        
        # Connect G1 (Pre: 0, Post: 1) as Exc (AMPA)
        net.sparse_connect(0, 1, Ionotropic(), jnp.array([ampa_gmax]))
        # Connect G2 (Pre: 1, Post: 0) as Inh (GABA)
        net.sparse_connect(1, 0, Ionotropic(), jnp.array([gaba_gmax]))
        
        # JIT compile and simulate 10ms
        net.make_trainable(["gmax_Ionotropic"])
        v = net.simulate(delta_t=0.1, t_max=10.0)
        return True, v
    except Exception as e:
        return False, str(e)


# ==========================================
# FASTAPI DASHBOARD
# ==========================================

@app.get("/")
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jaxley SDE Monitor</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@200;400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0a0a0b;
                --surface: rgba(20, 20, 22, 0.7);
                --border: #CFB87C;
                --accent: #9400D3;
                --text: #f0f0f0;
                --text-dim: #a0a0a0;
                --mono: 'JetBrains Mono', monospace;
                --sans: 'Inter', sans-serif;
            }
            body {
                background-color: var(--bg);
                color: var(--text);
                font-family: var(--sans);
                margin: 0;
                padding: 12px;
                height: 100vh;
                display: flex;
                flex-direction: column;
                gap: 12px;
                box-sizing: border-box;
            }
            .glass {
                background: var(--surface);
                backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: 4px;
            }
            .top-ribbon {
                height: 64px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 20px;
                flex-shrink: 0;
            }
            .main-grid {
                flex-grow: 1;
                display: grid;
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
                gap: 12px;
                min-height: 0;
            }
            .matrix-hero {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 12px;
            }
            .metric-card {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .label-tiny {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: var(--border);
                margin-bottom: 4px;
                font-weight: 600;
            }
            .odometer {
                font-family: var(--mono);
                font-size: 52px;
                font-weight: 200;
                color: var(--text);
            }
            .bottom-console {
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .console-header {
                background: rgba(207, 184, 124, 0.1);
                padding: 8px 16px;
                border-bottom: 1px solid var(--border);
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: var(--border);
                text-transform: uppercase;
            }
            .log-content {
                flex-grow: 1;
                font-family: var(--mono);
                font-size: 12px;
                padding: 12px;
                overflow-y: auto;
                line-height: 1.5;
                color: #88c0d0;
                background: rgba(0, 0, 0, 0.3);
            }
            .status-dot {
                width: 8px;
                height: 8px;
                background: var(--accent);
                border-radius: 50%;
                box-shadow: 0 0 8px var(--accent);
                display: inline-block;
                margin-right: 8px;
            }
            .loss { color: #bf616a; }
            .metric-group { display: flex; gap: 24px; font-family: var(--mono); padding-top:10px;}
            .metric-val { font-size: 20px; color: var(--accent); text-align:center;}
        </style>
    </head>
    <body>
        <div class="glass top-ribbon">
            <div style="font-weight: 600; letter-spacing: 0.1em; color: var(--border);">GAMMA // JAXLEY FED-LORA ORCHESTRATOR</div>
            <div style="font-family: var(--mono); font-size: 13px; color: var(--accent);">
                <div class="status-dot"></div><span id="system-status">Initializing</span> | Ep <span id="epoch-count">0</span>
            </div>
        </div>

        <div class="main-grid">
            <div class="matrix-hero">
                <div class="glass metric-card">
                    <div class="label-tiny">G1 Bio-Truth (z)</div>
                    <div><span class="odometer" id="z-val">0.00</span></div>
                </div>
                <div class="glass metric-card" style="border-color: var(--accent);">
                    <div class="label-tiny" style="color: var(--accent);">Eq. Council Loss</div>
                    <div><span class="odometer loss" id="loss-val">0.00</span></div>
                    <div class="metric-group">
                        <div><div class="label-tiny">Gain(x)</div><div class="metric-val" id="x-val">0.00</div></div>
                        <div><div class="label-tiny">Speed(y)</div><div class="metric-val" id="y-val">0.00</div></div>
                    </div>
                </div>
                <div class="glass metric-card">
                    <div class="label-tiny">G2 Bio-Truth (w)</div>
                    <div><span class="odometer" id="w-val">0.00</span></div>
                </div>
            </div>

            <div class="glass bottom-console">
                <div class="console-header"><span>SDE Live Telemetry</span></div>
                <div class="log-content" id="log-container"></div>
            </div>
        </div>
        <script>
            const evtSource = new EventSource("/stream");
            evtSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                document.getElementById('epoch-count').innerText = data.epoch;
                document.getElementById('system-status').innerText = data.status;
                document.getElementById('z-val').innerText = data.z.toFixed(3);
                document.getElementById('w-val').innerText = data.w.toFixed(3);
                document.getElementById('x-val').innerText = data.x.toFixed(3);
                document.getElementById('y-val').innerText = data.y.toFixed(3);
                document.getElementById('loss-val').innerText = data.loss.toFixed(3);
                const logContainer = document.getElementById('log-container');
                logContainer.innerHTML = data.logs.join('<br>');
                logContainer.scrollTop = logContainer.scrollHeight;
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

@app.get("/stream")
async def stream():
    q = asyncio.Queue()
    subscribers.append(q)
    async def event_generator():
        try:
            yield {"data": json.dumps(state)}
            while True:
                data = await q.get()
                yield {"data": data}
        except asyncio.CancelledError:
            subscribers.remove(q)
    return EventSourceResponse(event_generator())


# ==========================================
# AGENT LOGIC
# ==========================================

async def query_agent(client, agent_id, role_prompt, current_gmax, opp_gmax, mse):
    # Forced JSON output extraction
    payload = f"The current system MSE is {mse:.4f}. Your current gmax is {current_gmax}. The opposing agent's gmax is {opp_gmax}. You must propose a new gmax between 0.001 and 0.5 to fit the biophysics. Output ONLY valid JSON containing 'proposed_gmax' as a float."
    
    start_time = time.time()
    try:
        resp = await client.post(
            f"{LMSTUDIO_BASE_URL}/v1/chat/completions",
            json={
                "model": TARGET_MODEL,
                "messages": [
                    {"role": "system", "content": role_prompt},
                    {"role": "user", "content": payload}
                ],
                "temperature": 0.3,
                "max_tokens": 128,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        
        # Extract JSON float roughly
        match = re.search(r'"proposed_gmax"\s*:\s*([0-9.]+)', content)
        if match:
            val = float(match.group(1))
        else:
            val = current_gmax # Default if failed
            print(f"[{agent_id}] Failed to parse JSON: {content}")
            
        return {
            "id": agent_id,
            "gmax": min(max(val, 0.0), 10.0), # Cap hard limits
            "speed": time.time() - start_time,
            "success": True,
            "raw": content.replace('\n', ' ')
        }
    except Exception as e:
        print(f"[{agent_id}] Error: {e}")
        return {"id": agent_id, "gmax": current_gmax, "speed": 1.0, "success": False, "raw": ""}

async def game_loop():
    async with httpx.AsyncClient() as client:
        log("[Council] Synchronizing endpoint models...")
        
        target_v = jnp.array([[-65.0, -30.0, 10.0, -40.0, -65.0, -65.0]]) # Mock Target Trace

        # SDE Baselines
        gaba_val = 0.05
        ampa_val = 0.05
        current_mse = 999.0

        while True:
            state["epoch"] += 1
            state["status"] = "Generating Updates"
            broadcast_state()
            log(f"--- PREPARING FED-LORA EPOCH {state['epoch']} ---")

            g1_sys = "You are G1. You control the GABA (Inhibitory) synapse on a cell. Your objective is to discover a stable mathematical parameter."
            g2_sys = "You are G2. You control the AMPA (Excitatory) synapse on a cell. Your objective is to discover a stable mathematical parameter."

            g1_task = query_agent(client, "G1", g1_sys, gaba_val, ampa_val, current_mse)
            g2_task = query_agent(client, "G2", g2_sys, ampa_val, gaba_val, current_mse)

            res1, res2 = await asyncio.gather(g1_task, g2_task)

            if not res1["success"] or not res2["success"]:
                log("[SDE] Edge note timeout. Using momentum defaults.")
            else:
                gaba_val = res1["gmax"]
                ampa_val = res2["gmax"]

            log(f"[G1-GABA] Proposed -> {gaba_val:.4f} | Rationale: {res1['raw'][:50]}..")
            log(f"[G2-AMPA] Proposed -> {ampa_val:.4f} | Rationale: {res2['raw'][:50]}..")

            # Orchestrator Phase: Test the predictions
            state["status"] = "Jaxley Compilation"
            broadcast_state()

            comp_start = time.time()
            success, trace = run_simulation(gaba_val, ampa_val)
            comp_time = time.time() - comp_start
            
            # Y (Speed): Inverse of time taken
            state["y"] = 1.0 / max(comp_time, 0.001)

            if success:
                log(f"[A] Jaxley forward pass successful ({comp_time:.3f}s)")
                # Calculate X Component (Epistemic Gain / 1/MSE)
                mse = float(jnp.mean((trace[0, :6] - target_v)**2))
                state["x"] = max(100.0 - mse, 0.0) / 100.0  # Normalize metric
                current_mse = mse
                log(f"[A] Epistemic Gain (1-MSE) = {state['x']:.3f}")
                
                 # Calculate Bio-Thresholds (Z and W)
                state["z"] = 1.0 if (0.01 <= gaba_val <= 0.1) else 0.1
                state["w"] = 1.0 if (0.01 <= ampa_val <= 0.1) else 0.1
            else:
                log(f"[A] Jaxley crashed! {trace}")
                state["x"] = 0.0
                state["z"] = 0.0
                state["w"] = 0.0

            # Determine aggregate SDE loss
            state["loss"] = (state["z"] - state["w"])**2
            
            log(f"[SDE] Equilibirum Loss computed: {state['loss']:.4f}")
            state["status"] = "Distributing Proxy Updates"
            broadcast_state()

            await asyncio.sleep(4)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4321)
