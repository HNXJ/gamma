import asyncio
import logging
import sys
import json
from pathlib import Path

ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.extend([str(ROOT), str(ROOT / 'src')])

from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.structs import InferenceRequest

async def run_hardened_k3():
    logging.basicConfig(level=logging.ERROR) # Quiet logging for clean output
    
    registry = RuntimeRegistry(str(ROOT / 'configs'))
    model_key = 'gemma-4-e4b-it-mxfp8'
    model_spec = registry.load_model(model_key)
    
    scheduler = InferenceScheduler()
    backend = LMStudioBackend(base_url='http://127.0.0.1:1234')
    pool = SharedModelPool(model_spec, backend)
    await scheduler.register_pool(pool)

    agents = ['Alpha', 'Beta', 'Gamma']
    
    print(f'=== HARDENED K-3 TEST (n=3, Parallel Burst) ===')
    
    tasks = []
    for agent_name in agents:
        others = [a for a in agents if a != agent_name]
        prompt = (
            f'IDENTITY TEST: Your name is {agent_name}. '
            f'You are in a circle with exactly two others: {others[0]} and {others[1]}. '
            f'RESPONSE RULE: State your name and the names of the other two members. '
            f'DO NOT mention any other names. DO NOT mention Delta. '
            f'FORMAT: "I am [Name]. My colleagues are [Name1] and [Name2]."'
        )

        request = InferenceRequest(
            session_id='hardened-k3',
            agent_id=agent_name,
            model_key=model_key,
            messages=[{'role': 'user', 'content': prompt}],
            generation={'max_tokens': 30, 'temperature': 0.0}, # Max determinism
            adapter_stack=[]
        )
        tasks.append(scheduler.schedule(model_key, request))
    
    # LAUNCH SIMULTANEOUSLY
    print('Launching 3 simultaneous requests...')
    results = await asyncio.gather(*tasks)
    
    print('\n--- RAW RESPONSES ---')
    all_passed = True
    for i, res in enumerate(results):
        name = agents[i]
        text = res.text.strip()
        print(f'[{name}]: {text}')
        
        # STRICT VALIDATOR
        others = [a for a in agents if a != name]
        has_self = name in text
        has_others = all(o in text for o in others)
        has_delta = 'Delta' in text
        has_others_undeclared = any(x in text for x in ['Delta', 'Sigma', 'Omega', 'System', 'User'])
        
        if not has_self or not has_others or has_delta or has_others_undeclared:
            print(f'  >> VALIDATION FAILED for {name}')
            all_passed = False
        else:
            print(f'  >> VALIDATION PASSED')

    print('\n=== FINAL VERDICT ===')
    if all_passed:
        print('PASS: Identity isolation and parallel capability evidenced.')
    else:
        print('FAIL: Identity contamination or membership error detected.')

if __name__ == '__main__':
    asyncio.run(run_hardened_k3())
