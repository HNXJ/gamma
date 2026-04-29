import asyncio
import sys
import os
import json
from pathlib import Path

# Fix paths
root = Path('/Users/HN/MLLM/gamma')
sys.path.append(str(root / 'src'))
sys.path.append(str(root))

from gamma_runtime.tool_exec import PythonExecutor

async def main():
    executor = PythonExecutor(root)
    
    proposal_id = "STABILITY_CHUNK_001"
    payload = {
        "proposal_id": proposal_id,
        "seed_pair": 42,
        "healthy_params": {
            "pv_gain": 1.4553,
            "pc_to_pv_w": 1.0,
            "pv_to_pc_w": 1.0,
            "pv_to_pv_w": 1.0,
            "drive_amp": 0.224
        },
        "schiz_params": {
            "pv_gain": 0.63,
            "pc_to_pv_w": 1.5,
            "pv_to_pc_w": 0.3,
            "pv_to_pv_w": 1.8,
            "drive_amp": 0.2
        },
        "rationale": "Controlled descent chunk 001. Applying drive_amp * 0.8 and pv_gain * 1.05 to both regimes to reach v_max < 80mV target."
    }
    
    print(f"Executing {proposal_id}...")
    result = await executor.execute(payload)
    
    result_path = os.path.join(root, 'local/game001/results', f'{proposal_id}.json')
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Update proposals.jsonl
    proposal_entry = {
        "proposal_id": proposal_id,
        "status": "completed",
        "payload": payload,
        "result_path": result_path
    }
    with open(os.path.join(root, 'local/game001/proposals.jsonl'), 'a') as f:
        f.write(json.dumps(proposal_entry) + '\n')
        
    print(f"Result saved to {result_path}")
    # Print a summary of metrics
    h = result.get('metadata', {}).get('healthy_stability', {})
    s = result.get('metadata', {}).get('schiz_stability', {})
    print(f"METRICS_SUMMARY: healthy_v_max={h.get('v_max')}, schiz_v_max={s.get('v_max')}, healthy_fr={h.get('firing_rate')}, schiz_fr={s.get('firing_rate')}, status={result.get('status')}")

if __name__ == "__main__":
    asyncio.run(main())
