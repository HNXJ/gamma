import asyncio
import logging
from pathlib import Path
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.orchestrator import UnifiedOrchestrator

async def main():
    root = Path('/Users/HN/MLLM/gamma')
    registry = RuntimeRegistry(root / 'configs')
    
    # Passing registry to scheduler for AUTO-PROVISIONING
    scheduler = InferenceScheduler(registry=registry)
    
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    
    print("--- Launching Council Proof (Round 1) ---")
    game_id = await orchestrator.launch_run(
        run_type="council",
        topic="E-I firing rate balancing with natural frequency tuning toward 30 Hz",
        game_id="proof001",
        rounds=1
    )
    print(f"Game ID: {game_id}")
    
    print("Deliberation in progress...")
    await asyncio.sleep(120) 
    print("Proof script finished execution.")

if __name__ == "__main__":
    asyncio.run(main())
