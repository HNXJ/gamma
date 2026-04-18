#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "asyncio",
#     "tiktoken"
# ]
# ///

import asyncio
import httpx
import json
import time
import sys

LMSTUDIO_BASE_URL = "http://127.0.0.1:1234"
TARGET_MODEL = "gemma-4-e4b-agentic-opus-reasoning-geminicli-mlx"
FALLBACK_MODEL = "gemma-4-e4b-it-mxfp8"

# The state-value metrics for the council
# z: G1 Info Density
# w: G2 Info Density
# x: Quality (Synthesized for now as 1.0 if both respond)
# y: Throughput (Tokens per second across system)

async def load_model(client, model_key):
    print(f"[Council] Requesting 128K dual-slot allocation for {model_key}...")
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
            print(f"[Council] Load error: {data['error']['message']}")
            return False
        print(f"[Council] Loaded {model_key} successfully in {data.get('load_time_seconds', '?')}s.")
        return True
    except Exception as e:
        print(f"[Council] Load exception: {e}")
        return False

async def query_agent(client, model_key, agent_id, system_msg, payload):
    print(f"[{agent_id}] Processing payload of length {len(payload)} chars...")
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
        completion_t = usage.get("completion_tokens", 1)
        
        # Calculate compression ratio (Output length vs Input length)
        # Higher means looser compression. Lower means tighter.
        # We want density: (Input Tokens / Output Tokens)
        density = prompt_t / max(completion_t, 1)
        throughput = (prompt_t + completion_t) / elapsed
        
        print(f"[{agent_id}] Done in {elapsed:.2f}s | Speed: {throughput:.1f} t/s | Density: {density:.2f}x")
        
        return {
            "id": agent_id,
            "content": content,
            "density": density,
            "speed": throughput,
            "success": True
        }
    except Exception as e:
        print(f"[{agent_id}] Failed: {e}")
        return {"id": agent_id, "success": False, "density": 0.0, "speed": 0.0}

async def run_council():
    async with httpx.AsyncClient() as client:
        # 1. Unload all to ensure fresh RAM
        print("[Council] Clearing VRAM...")
        try:
            await client.get(f"{LMSTUDIO_BASE_URL}/api/v1/models")
            # For simplicity, we just rely on loading new overriding, or you can explicitly unload
        except:
            pass

        # 2. Try loading primary, then fallback
        model_to_use = TARGET_MODEL
        success = await load_model(client, model_to_use)
        if not success:
            print(f"[Council] Falling back to {FALLBACK_MODEL} (likely due to MLX format compat limits)...")
            model_to_use = FALLBACK_MODEL
            success = await load_model(client, model_to_use)
            if not success:
                print("[Council] FATAL: Could not load any models.")
                sys.exit(1)

        print("\n=== COUNCIL SESSION INITIATED ===")
        print("Equilibrium Objective: Minimize (z - w)^2")
        print("System Objectives: Maximize z, w such that z > x+y and w > x+y\n")

        # Create massive synthetic payload for context stress
        # Let's generate a ~20,000 word dummy codebase/math text
        base_text = "def calculate_manifold(tensor_a, tensor_b):\n    # Simulate n-dimensional scaling\n    return tensor_a @ tensor_b.T\n"
        huge_payload = base_text * 1500  # Synthesizing ~40,000 tokens to fit safely within the 64k memory constraint
        
        chunk_1 = huge_payload + "\n\nTask: Find the algorithmic complexity of the manifold projection described above, state your reasoning, and compress the core insight into exactly one paragraph."
        chunk_2 = huge_payload + "\n\nTask: Find the memory complexity of the manifold projection described above, state your reasoning, and compress the core insight into exactly one paragraph."

        sys_prompt = "You are a highly efficient neural compressor. Digest the data, solve the problem, and output the maximum information density possible."

        # Spawn G1 and G2 in parallel
        # This will utilize the parallel=2 slots allocated in LM Studio
        g1_task = query_agent(client, model_to_use, "G1", sys_prompt, chunk_1)
        g2_task = query_agent(client, model_to_use, "G2", sys_prompt, chunk_2)

        results = await asyncio.gather(g1_task, g2_task)
        
        if not all(r["success"] for r in results):
            print("\n[Council] Simulation failed due to agent timeout/error.")
            return

        g1_res, g2_res = results

        # 4. Calculate Game Theory States
        z = g1_res["density"]
        w = g2_res["density"]
        
        # Normalize variables for comparison 
        # x: Quality (baseline 1.0, +1 per agent success)
        x = 2.0 
        
        # y: System throughput (normalized to K-tokens/sec)
        sys_speed = g1_res["speed"] + g2_res["speed"]
        y = sys_speed / 1000.0  

        loss = (z - w)**2

        print("\n=== STATE-VALUE RESULTS ===")
        print(f"z (G1 Density):  {z:.2f}x compression")
        print(f"w (G2 Density):  {w:.2f}x compression")
        print(f"x (Quality):     {x:.2f}")
        print(f"y (Throughput):  {y:.2f} Kt/s")
        print("-" * 25)
        print(f"Equilibrium Loss (z - w)^2 : {loss:.2f}")
        print(f"Constraint (z > x + y)     : {'PASS' if z > (x + y) else 'FAIL'} ({z:.2f} > {(x+y):.2f})")
        print(f"Constraint (w > x + y)     : {'PASS' if w > (x + y) else 'FAIL'} ({w:.2f} > {(x+y):.2f})")
        
        print("\n=== AGENT SUMMARIES ===")
        print(f"G1 Response => {g1_res['content'][:150]}...")
        print(f"G2 Response => {g2_res['content'][:150]}...")
        
if __name__ == "__main__":
    asyncio.run(run_council())
