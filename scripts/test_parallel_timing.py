import asyncio
import time
import sys
from pathlib import Path

ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.extend([str(ROOT), str(ROOT / 'src')])

from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.structs import InferenceRequest

async def time_request(scheduler, model_key, agent_id):
    req = InferenceRequest(
        session_id='timing-test',
        agent_id=agent_id,
        model_key=model_key,
        messages=[{'role': 'user', 'content': 'Say exactly: Hello.'}],
        generation={'max_tokens': 5},
        adapter_stack=[]
    )
    start = time.time()
    res = await scheduler.schedule(model_key, req)
    end = time.time()
    return agent_id, start, end, res.text.strip()

async def run_timing_test():
    registry = RuntimeRegistry(str(ROOT / 'configs'))
    model_key = 'gemma-4-e4b-it-mxfp8'
    model_spec = registry.load_model(model_key)
    scheduler = InferenceScheduler()
    backend = LMStudioBackend(base_url='http://127.0.0.1:1234')
    pool = SharedModelPool(model_spec, backend)
    await scheduler.register_pool(pool)

    print('Launching 3 simultaneous requests for timing audit...')
    tasks = [time_request(scheduler, model_key, f'Agent-{i}') for i in range(3)]
    results = await asyncio.gather(*tasks)
    
    # Analyze overlap
    results.sort(key=lambda x: x[1]) # Sort by start time
    for agent_id, start, end, text in results:
        duration = end - start
        print(f'{agent_id}: Start={start:.4f}, End={end:.4f}, Duration={duration:.4f}s')

if __name__ == '__main__':
    asyncio.run(run_timing_test())
