import urllib.request
import json
import os
import concurrent.futures

MODEL_ID = "gemma-4-26b-a4b-it"
BACKEND_URL = "http://127.0.0.1:1234/v1/chat/completions"
AGENT_COUNT = 16
PACKET_DIR = r"D:\workspace\gemini-gamma-labyrinth\repos\gamma\outputs\tournament\week2_jaxfne_inventory_audit_grounded\evidence_packets"
OUTPUT_DIR = r"D:\workspace\gemini-gamma-labyrinth\repos\gamma\outputs\tournament\week2_jaxfne_inventory_audit_grounded"

def call_gemma(agent_id, packet_path):
    with open(packet_path, "r", encoding="utf-8") as f:
        evidence_content = f.read()
        
    full_prompt = (
        f"You are {agent_id} in Gamma Labyrinth Week 2 (Grounded Rerun).\n\n"
        "Mission: JAXFNE Craft Inventory Grounded Audit.\n\n"
        "Constraint: Perform a bounded audit based on the PROVIDED EVIDENCE PACKET below. "
        "Do not run biological simulations. Do not install dependencies. Do not mutate truth. "
        "Keep interpretation truth_safe_unverified. If evidence is missing, report it as a gap.\n\n"
        "--- EVIDENCE PACKET START ---\n"
        f"{evidence_content}\n"
        "--- EVIDENCE PACKET END ---\n\n"
        "Output a short Markdown report including: files inspected, grounded findings (using evidence from packet), risks, and a pass/revise/block decision."
    )
    
    try:
        data = json.dumps({
            'model': MODEL_ID,
            'messages': [{'role': 'user', 'content': full_prompt}],
            'max_tokens': 1536,
            'temperature': 0
        }).encode('utf-8')
        req = urllib.request.Request(BACKEND_URL, data=data, headers={'Content-Type': 'application/json'})
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return agent_id, True, result['choices'][0]['message']['content']
    except Exception as e:
        return agent_id, False, f"ERROR: {str(e)}"

def orchestrate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=AGENT_COUNT) as executor:
        futures = []
        for i in range(AGENT_COUNT):
            agent_id = f"agent_{i+1:02d}"
            packet_path = os.path.join(PACKET_DIR, f"{agent_id}_evidence_packet.md")
            futures.append(executor.submit(call_gemma, agent_id, packet_path))
            
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    # Save reports
    for agent_id, success, content in results:
        report_path = os.path.join(OUTPUT_DIR, f"{agent_id}_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
                
    print(f"DONE: Generated {len(results)} grounded reports in {OUTPUT_DIR}")

if __name__ == "__main__":
    orchestrate()
