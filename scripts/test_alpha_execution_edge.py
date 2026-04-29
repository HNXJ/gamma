import asyncio
import os
import json
import time
import sys

ROOT = '/Users/HN/MLLM/gamma'
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, 'src'))
sys.path.append('/Users/HN/MLLM/jbiophysic/src')

from gamma_runtime.bridge.v1_gamma_bridge import V1GammaBridge

class MockBB:
    async def add_entry(self, sender, content, metadata=None):
        print('[BLACKBOARD] {}: {}'.format(sender, content))

async def test_execution_edge():
    bb = MockBB()
    bridge = V1GammaBridge(bb, enabled=True)
    
    prop_file = '/Users/HN/MLLM/gamma/local/game001/proposals.jsonl'
    if os.path.exists(prop_file): os.remove(prop_file)
    
    result_path = '/Users/HN/MLLM/gamma/local/game001/results/R1_v1_gamma_proponent.json'
    if os.path.exists(result_path): os.remove(result_path)

    proposal_data = {
        'healthy_params': {'pv_gain': 1.0, 'drive_amp': 0.1},
        'schiz_params': {'pv_gain': 0.5, 'drive_amp': 0.1},
        'seed_pair': 42,
        'rationale': 'ALPHA test of execution edge.'
    }
    proposal_text = 'I suggest this config:\n'.format(json.dumps(proposal_data))
    
    print('--- Step 1: Bridge Normalization & Enqueue ---')
    await bridge.process_proposal('v1_gamma_proponent', proposal_text, 1)
    
    print('\n--- Step 2: Waiting for Science Worker (polling) ---')
    for i in range(60):
        if os.path.exists(result_path):
            print('SUCCESS: Scientific Result Found!')
            with open(result_path, 'r') as f:
                res = json.load(f)
                # Res matches ScientificResult dataclass dict
                print('Status: {}'.format(res.get('status')))
                # Pipeline returns metrics in results dict
                h_sup = res.get('healthy', {}).get('sup', {}).get('gamma_ratio')
                s_sup = res.get('schiz', {}).get('sup', {}).get('gamma_ratio')
                print('Healthy Ratio (sup): {}'.format(h_sup))
                print('Schiz Ratio (sup): {}'.format(s_sup))
            break
        if i % 5 == 0: print('Waiting... {}s'.format(i*2))
        await asyncio.sleep(2)
    else:
        print('TIMEOUT: Worker did not produce result.')
        print('\n--- Worker Log ---')
        log_path = '/Users/HN/MLLM/gamma/local/game001/logs/science_worker.log'
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                print(f.read())

if __name__ == '__main__':
    asyncio.run(test_execution_edge())
