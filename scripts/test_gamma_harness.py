import sys
import os
import json
import asyncio
from pathlib import Path

# Canonical Path Setup
ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.extend([str(ROOT), str(ROOT / 'src'), '/Users/HN/MLLM/jbiophysic/src'])

from gamma_runtime.bridge.proposal_normalizer import ProposalNormalizer
from gamma_runtime.bridge.bridge_contract import ProposalPayload
from gamma_runtime.bridge.v1_gamma_bridge import V1GammaBridge

class MockBB:
    async def add_entry(self, sender, content, metadata=None):
        print(f'[MOCK BB] {sender}: {content[:100]}...')

async def run_harness():
    print('--- GATE 1: PROPOSAL NORMALIZATION ---')
    proposal_id = 'GAMMA_TEST_001'
    raw_text = '''
    I propose:
    ```json
    {
        "healthy_params": {"pv_gain": 1.0, "drive_amp": 0.1},
        "schiz_params": {"pv_gain": 0.5, "drive_amp": 0.1},
        "seed_pair": 42,
        "rationale": "GAMMA harness test."
    }
    ```
    '''
    payload = ProposalNormalizer.normalize(raw_text, proposal_id)
    if not payload:
        print('FAIL: Normalization rejected proposal.')
        return
    print('PASS: Normalization successful.')

    print('\n--- GATE 2: DURABLE ENQUEUE ---')
    bb = MockBB()
    bridge = V1GammaBridge(bb, enabled=True)
    # Ensure logs dir exists
    (ROOT / 'local/game001/logs').mkdir(parents=True, exist_ok=True)
    
    # Use a specific test proposal file
    bridge.proposals_file = ROOT / 'local/game001/proposals.jsonl'
    if bridge.proposals_file.exists(): bridge.proposals_file.unlink()
    
    await bridge.process_proposal('v1_gamma_proponent', raw_text, 1)
    
    if bridge.proposals_file.exists():
        with open(bridge.proposals_file, 'r') as f:
            entry = json.loads(f.readline())
            print(f'PASS: Enqueued proposal_id: {entry["proposal_id"]}')
    else:
        print('FAIL: proposals.jsonl not created.')
        return

    print('\n--- GATE 3 & 4: WORKER CONSUMPTION & RESULT ---')
    result_path = ROOT / 'local/game001/results' / f'R1_v1_gamma_proponent.json'
    
    print(f'Watching for result at: {result_path}')
    for i in range(30): 
        if result_path.exists():
            print('PASS: Result artifact found.')
            with open(result_path, 'r') as f:
                res = json.load(f)
                if 'healthy' in res and 'sup' in res['healthy']:
                    print('PASS: Non-placeholder metrics detected.')
                    print(f'Sample: Healthy Sup Gamma Ratio = {res["healthy"]["sup"]["gamma_ratio"]}')
                else:
                    print('FAIL: Result contains placeholders or is malformed.')
            break
        if i % 5 == 0: print(f'Waiting for ScienceWorker... {i*2}s')
        await asyncio.sleep(2)
    else:
        print('FAIL: Timeout. Check local/game001/logs/worker.log')

if __name__ == '__main__':
    asyncio.run(run_harness())
