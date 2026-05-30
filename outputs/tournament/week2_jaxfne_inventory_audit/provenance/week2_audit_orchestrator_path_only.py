import urllib.request
import json
import os
import concurrent.futures
from datetime import datetime

MODEL_ID = "gemma-4-26b-a4b-it"
BACKEND_URL = "http://127.0.0.1:1234/v1/chat/completions"
AGENT_COUNT = 16
OUTPUT_DIR = r"D:\workspace\gemini-gamma-labyrinth\repos\gamma\outputs\tournament\week2_jaxfne_inventory_audit"

ROLES = [
    "Agent 01: source-to-field tensor bridge contract audit",
    "Agent 02: emitter/readout contract audit",
    "Agent 03: placeholder-fails-loudly audit",
    "Agent 04: JAX trace-safety audit",
    "Agent 05: JSON-safe manifest/report audit",
    "Agent 06: local smoke-test design",
    "Agent 07: Jaxley boundary and optional bridge review",
    "Agent 08: JAXFNE package/import/runtime discovery",
    "Agent 09: documentation-to-code contract map",
    "Agent 10: test coverage gap map",
    "Agent 11: artifact manifest schema check",
    "Agent 12: command/provenance capture check",
    "Agent 13: negative-result preservation design",
    "Agent 14: tournament scoring ledger draft",
    "Agent 15: THETA validation checklist draft",
    "Agent 16: integration judge / synthesis report"
]

FILES_TO_INSPECT = [
    "jaxfne/core.py", "jaxfne/emitters.py", "jaxfne/fields.py", "jaxfne/bridges.py",
    "jaxfne/runtime.py", "jaxfne/io.py", "jaxfne/objectives.py", "jaxfne/validation.py",
    "tests/test_jaxley_bridge.py", "examples/03_jaxley_bridge_smoke.py"
]

def call_gemma(agent_id, role, prompt_text):
    full_prompt = (
        f"You are {agent_id} in Gamma Labyrinth Week 2. Role: {role}\n\n"
        "Mission: JAXFNE Craft Inventory Audit.\n"
        f"Current objective: {role}\n\n"
        "Constraint: Perform a bounded audit of the codebase/inventory based on your role. "
        "Do not run biological simulations. Do not install dependencies. Do not mutate truth. "
        "Keep interpretation truth_safe_unverified.\n\n"
        f"Prompt context: {prompt_text}\n\n"
        "Output a short Markdown report including: files inspected, findings, risks, and a pass/revise/block decision."
    )
    
    try:
        data = json.dumps({
            'model': MODEL_ID,
            'messages': [{'role': 'user', 'content': full_prompt}],
            'max_tokens': 1024,
            'temperature': 0
        }).encode('utf-8')
        req = urllib.request.Request(BACKEND_URL, data=data, headers={'Content-Type': 'application/json'})
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return agent_id, True, result['choices'][0]['message']['content']
    except Exception as e:
        return agent_id, False, str(e)

def orchestrate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=AGENT_COUNT) as executor:
        futures = []
        for i in range(AGENT_COUNT):
            agent_id = f"gamma_jaxfne_week2_agent_{i+1:02d}"
            role = ROLES[i]
            # Simple placeholder for role-specific context to keep this bounded
            prompt_text = f"Perform audit for {role}. Focus on file paths: {', '.join(FILES_TO_INSPECT)}"
            futures.append(executor.submit(call_gemma, agent_id, role, prompt_text))
            
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    # Save reports
    for agent_id, success, content in results:
        report_path = os.path.join(OUTPUT_DIR, f"{agent_id}_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            if success:
                f.write(content)
            else:
                f.write(f"FAILED TO GENERATE REPORT: {content}")
                
    print(f"DONE: Generated {len(results)} reports in {OUTPUT_DIR}")

if __name__ == "__main__":
    orchestrate()
