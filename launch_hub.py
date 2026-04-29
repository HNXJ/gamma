import asyncio
import logging
from pathlib import Path
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.orchestrator import UnifiedOrchestrator
from gamma_runtime.hub_api import HubAPIServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Launcher')

async def main():
    root = Path('/Users/HN/MLLM/gamma')
    registry = RuntimeRegistry(root / 'configs')
    
    # Enable Auto-Provisioning by passing registry
    scheduler = InferenceScheduler(registry=registry)
    
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    
    server = HubAPIServer(orchestrator, port=8001)
    server.start()
    
    logger.info('Gamma Hub & Orchestrator live. Auto-launching game001...')
    
    # Auto-launch persistent mission for game001
    await orchestrator.launch_run(
        'council', 
        'Grounded Bootstrap Mission: Stabilize 10-neuron Circuit', 
        game_id='game001',
        rounds=5
    )
    
    logger.info('Persistent mission launched. Monitoring for idleness...')
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
