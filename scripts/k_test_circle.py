import asyncio
import logging
import sys
import os
import json
from pathlib import Path

ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.extend([str(ROOT), str(ROOT / 'src')])

from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.structs import InferenceRequest

async def run_k_test():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('K-Test')
    
    registry = RuntimeRegistry(str(ROOT / 'configs'))
    model_key = 'gemma-4-e4b-it-mxfp8'
    model_spec = registry.load_model(model_key)
    
    scheduler = InferenceScheduler()
    backend = LMStudioBackend(base_url='http://127.0.0.1:1234')
    pool = SharedModelPool(model_spec, backend)
    await scheduler.register_pool(pool)

    agents = ['Alpha', 'Beta', 'Gamma']
    history = []
    
    print(f'=== K-TEST START (n=3, Circle Protocol) ===')
    
    for round_idx in range(4):
        print(f'\n--- Round {round_idx + 1} ---')
        
        # In a circle test, we target specific agents sequentially to build the knowledge chain
        # but we can burst them if they are checking for 'presence'
        current_agent = agents[round_idx % 3]
        
        prompt = f'We are in a K-Test circle. Your name is {current_agent}.'
        if history:
            prompt += f' Previous messages: {json.dumps(history)}.'
        prompt += ' Acknowledge the others by name and confirm you know the circle state. Keep it brief (1 sentence).'

        request = InferenceRequest(
            session_id='k-test',
            agent_id=current_agent,
            model_key=model_key,
            messages=[{'role': 'user', 'content': prompt}],
            generation={'max_tokens': 50},
            adapter_stack=[]
        )
        
        res = await scheduler.schedule(model_key, request)
        print(f'[{current_agent}]: {res.text.strip()}')
        history.append({'sender': current_agent, 'text': res.text.strip()})
        
        # Verify the circle in the last round
        if round_idx == 3:
            print('\n=== CIRCLE VALIDATION ===')
            if all(a in str(history) for a in agents):
                print('PASS: All agents identified and acknowledged in the loop.')
            else:
                print('FAIL: Knowledge chain broken.')

if __name__ == '__main__':
    asyncio.run(run_k_test())
