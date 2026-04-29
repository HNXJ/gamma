import asyncio
import logging
import sys
import os
from pathlib import Path

ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.extend([str(ROOT), str(ROOT / 'src')])

from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.tool_loop import execute_tool_loop

async def run_test():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('HybridTest')
    
    registry = RuntimeRegistry(str(ROOT / 'configs'))
    model_key = 'gemma-4-e4b-it-mxfp8'
    model_spec = registry.load_model(model_key)
    
    scheduler = InferenceScheduler()
    backend = LMStudioBackend(base_url='http://127.0.0.1:1234')
    pool = SharedModelPool(model_spec, backend)
    await scheduler.register_pool(pool)

    agent = registry.get_agent('v1_gamma_proponent')
    
    messages = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": "Start by using python to calculate the square root of 12345. Then discuss the result and why it matters for our V1 model."}
    ]
    
    print('=== HYBRID TOOL LOOP TEST ===')
    final_response = await execute_tool_loop(
        scheduler, agent, messages, 'test-session', logger
    )
    
    print('\n--- FINAL DELIBERATION ---')
    print(final_response)

if __name__ == '__main__':
    asyncio.run(run_test())
