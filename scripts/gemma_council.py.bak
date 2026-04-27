#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "asyncio",
#     "tiktoken",
#     "fastapi",
#     "uvicorn",
#     "sse-starlette"
# ]
# ///

import asyncio
import httpx
import json
import time
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

app = FastAPI()

LMSTUDIO_BASE_URL = "http://127.0.0.1:1234"
TARGET_MODEL = "gemma-4-e4b-agentic-opus-reasoning-geminicli-mlx"
FALLBACK_MODEL = "gemma-4-e4b-it-mxfp8"

# Global state for the UI
state = {
    "epoch": 0,
    "z1": 0.0,
    "z2": 0.0,
    "z3": 0.0,
    "z4": 0.0,
    "x": 4.0,  # Baseline
    "y": 0.0,
    "loss": 0.0,
    "logs": ["[System] Booting Quad-Gemma Council..."],
    "status": "Initializing"
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

@app.get("/")
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gemma Council Monitor</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@200;400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0a0a0b;
                --surface: rgba(20, 20, 22, 0.7);
                --border: #CFB87C;
                --accent: #9400D3;
                --text: #f0f0f0;
                --text-dim: #a0a0a0;
                --mono: 'JetBrains Mono', 'Courier New', monospace;
                --sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
                -webkit-backdrop-filter: blur(12px);
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
                grid-template-columns: 1fr 1fr;
                grid-template-rows: auto auto;
                gap: 12px;
            }
            .system-card {
                grid-column: 1 / -1;
                border-color: var(--accent);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 12px;
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
                font-size: 48px;
                font-weight: 200;
                color: var(--text);
            }
            .unit {
                font-size: 14px;
                color: var(--text-dim);
                margin-left: 4px;
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
                text-transform: uppercase;
                color: var(--border);
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
            .status-badge {
                display: flex;
                align-items: center;
                gap: 8px;
                font-family: var(--mono);
                font-size: 13px;
                color: var(--accent);
            }
            .status-dot {
                width: 8px;
                height: 8px;
                background: var(--accent);
                border-radius: 50%;
                box-shadow: 0 0 8px var(--accent);
            }
            .metric-group {
                display: flex;
                justify-content: center;
                gap: 24px;
                font-family: var(--mono);
            }
            .metric-small {
                text-align: center;
            }
            .metric-val {
                font-size: 20px;
                color: var(--accent);
            }
            .loss {
                color: #bf616a;
            }
        </style>
    </head>
    <body>
        <div class="glass top-ribbon">
            <div style="font-weight: 600; letter-spacing: 0.05em; color: var(--border);">GAMMA // QUAD-COUNCIL</div>
            <div class="status-badge">
                <div class="status-dot"></div>
                <span id="system-status">Initializing</span> | Epoch <span id="epoch-count">0</span>
            </div>
        </div>

        <div class="main-grid">
            <div class="glass system-card">
                <div class="metric-group">
                    <div class="metric-small"><div class="label-tiny" style="color: var(--accent);">Eq. Variance Loss</div><div><span class="odometer loss" style="font-size:32px;" id="loss-val">0.00</span></div></div>
                    <div class="metric-small"><div class="label-tiny">Target (x)</div><div class="metric-val" id="x-val">4.0</div></div>
                    <div class="metric-small"><div class="label-tiny">Speed (y)</div><div class="metric-val" id="y-val">0.0</div></div>
                </div>
            </div>
            <div class="matrix-hero">
                <div class="glass metric-card">
                    <div class="label-tiny">G1 Density (z1)</div>
                    <div><span class="odometer" id="z1-val">0.00</span><span class="unit">x</span></div>
                </div>
                <div class="glass metric-card">
                    <div class="label-tiny">G2 Density (z2)</div>
                    <div><span class="odometer" id="z2-val">0.00</span><span class="unit">x</span></div>
                </div>
                <div class="glass metric-card">
                    <div class="label-tiny">G3 Density (z3)</div>
                    <div><span class="odometer" id="z3-val">0.00</span><span class="unit">x</span></div>
                </div>
                <div class="glass metric-card">
                    <div class="label-tiny">G4 Density (z4)</div>
                    <div><span class="odometer" id="z4-val">0.00</span><span class="unit">x</span></div>
                </div>
            </div>

            <div class="glass bottom-console">
                <div class="console-header">
                    <span>Active Telemetry & Context Stream</span>
                </div>
                <div class="log-content" id="log-container">
                    <!-- Logs go here -->
                </div>
            </div>
        </div>

        <script>
            const evtSource = new EventSource("/stream");
            
            evtSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                document.getElementById('epoch-count').innerText = data.epoch;
                document.getElementById('system-status').innerText = data.status;
                
                document.getElementById('z1-val').innerText = data.z1.toFixed(2);
                document.getElementById('z2-val').innerText = data.z2.toFixed(2);
                document.getElementById('z3-val').innerText = data.z3.toFixed(2);
                document.getElementById('z4-val').innerText = data.z4.toFixed(2);
                document.getElementById('x-val').innerText = data.x.toFixed(2);
                document.getElementById('y-val').innerText = data.y.toFixed(2);
                document.getElementById('loss-val').innerText = data.loss.toFixed(2);
                
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
            # Send initial state immediately
            yield {"data": json.dumps(state)}
            while True:
                data = await q.get()
                yield {"data": data}
        except asyncio.CancelledError:
            subscribers.remove(q)
    
    return EventSourceResponse(event_generator())


async def load_model(client, model_key):
    log(f"[Council] Requesting allocation for {model_key}...")
    state["status"] = "Loading Model"
    broadcast_state()
    try:
        resp = await client.post(
            f"{LMSTUDIO_BASE_URL}/api/v1/models/load",
            json={
                "model": model_key,
                "context_length": 64000,
                "echo_load_config": True,
            },
            timeout=180.0,
        )
        data = resp.json()
        if "error" in data:
            log(f"[Council] Load error: {data['error']['message']}")
            return False
        log(f"[Council] Loaded {model_key} successfully.")
        return True
    except Exception as e:
        log(f"[Council] Load exception: {e}")
        return False

async def query_agent(client, model_key, agent_id, system_msg, payload):
    log(f"[{agent_id}] Processing {len(payload)} chars...")
    start_time = time.time()
    
    try:
        resp = await client.post(
            f"{LMSTUDIO_BASE_URL}/v1/chat/completions",
            json={
                "model": model_key,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": payload}
                ],
                "temperature": 0.1,
                "max_tokens": 1024,
            },
            timeout=300.0,
        )
        resp.raise_for_status()
        data = resp.json()
        
        elapsed = time.time() - start_time
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        prompt_t = usage.get("prompt_tokens", 1)
        completion_t = max(usage.get("completion_tokens", 1), 1)
        
        density = (prompt_t / completion_t) if completion_t > 0 else 0
        throughput = (prompt_t + completion_t) / elapsed
        
        log(f"[{agent_id}] Done in {elapsed:.1f}s | Den: {density:.1f}x")
        
        return {
            "id": agent_id,
            "content": content,
            "density": density,
            "speed": throughput,
            "success": True
        }
    except Exception as e:
        log(f"[{agent_id}] Failed HTTP: {e}")
        return {"id": agent_id, "success": False, "density": 0.0, "speed": 0.0}

async def game_loop():
    async with httpx.AsyncClient() as client:
        log("[Council] Clearing VRAM...")
        try:
            await client.get(f"{LMSTUDIO_BASE_URL}/api/v1/models")
        except:
            pass

        model_to_use = TARGET_MODEL
        success = await load_model(client, model_to_use)
        if not success:
            log(f"[Council] Falling back to {FALLBACK_MODEL}...")
            model_to_use = FALLBACK_MODEL
            success = await load_model(client, model_to_use)
            if not success:
                log("[Council] FATAL: Could not load any models.")
                return

        base_text = "def calculate_manifold(tensor_a, tensor_b):\n    # Simulate n-dimensional scaling\n    return tensor_a @ tensor_b.T\n"
        huge_payload = base_text * 3000  # Synthesizing ~80,000 tokens for 128GB massive stress testing
        sys_prompt = "You are a highly efficient neural compressor. Digest the data, solve the problem, and output the maximum information density possible."

        while True:
            state["epoch"] += 1
            state["status"] = "Generating"
            broadcast_state()
            log(f"--- STARTING EPOCH {state['epoch']} ---")

            chunk_1 = huge_payload + f"\n\nTask: Epoch {state['epoch']}. Algorithmic complexity of manifold projection. Compress to 1 chunk. Last density: {state['z1']:.2f}."
            chunk_2 = huge_payload + f"\n\nTask: Epoch {state['epoch']}. Memory complexity of manifold projection. Compress to 1 chunk. Last density: {state['z2']:.2f}."
            chunk_3 = huge_payload + f"\n\nTask: Epoch {state['epoch']}. Tensor operation gradient flow. Compress to 1 chunk. Last density: {state['z3']:.2f}."
            chunk_4 = huge_payload + f"\n\nTask: Epoch {state['epoch']}. Hardware execution bottlenecks. Compress to 1 chunk. Last density: {state['z4']:.2f}."

            g1_task = query_agent(client, model_to_use, "G1", sys_prompt, chunk_1)
            g2_task = query_agent(client, model_to_use, "G2", sys_prompt, chunk_2)
            g3_task = query_agent(client, model_to_use, "G3", sys_prompt, chunk_3)
            g4_task = query_agent(client, model_to_use, "G4", sys_prompt, chunk_4)

            results = await asyncio.gather(g1_task, g2_task, g3_task, g4_task)
            
            if not all(r["success"] for r in results):
                log("[Council] Agent failure detected. Retrying next epoch...")
                await asyncio.sleep(5)
                continue

            g1_res, g2_res, g3_res, g4_res = results

            # Update state with Game Theory results
            state["z1"] = g1_res["density"]
            state["z2"] = g2_res["density"]
            state["z3"] = g3_res["density"]
            state["z4"] = g4_res["density"]
            state["x"] = 4.0 
            sys_speed = sum(r["speed"] for r in results)
            state["y"] = sys_speed / 1000.0  
            
            # Variance Loss calculation over elements z1..z4
            densities = [state["z1"], state["z2"], state["z3"], state["z4"]]
            mean = sum(densities) / 4
            state["loss"] = sum((d - mean)**2 for d in densities) / 4
            
            state["status"] = "Analyzing Feedback"

            log(f"Variance Loss: {state['loss']:.2f} | Speed: {state['y']:.3f} Kt/s")
            
            # Show a snippet of their output
            log(f"[G1-Out] {g1_res['content'][:60]}...")
            log(f"[G2-Out] {g2_res['content'][:60]}...")
            log(f"[G3-Out] {g3_res['content'][:60]}...")
            log(f"[G4-Out] {g4_res['content'][:60]}...")

            broadcast_state()
            await asyncio.sleep(5)  # Pause between epochs


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(game_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4321)
