import asyncio
import sys
import os
from pathlib import Path

# Add src and current dir to path
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from gamma_runtime.structs import ModelSpec, InferenceResult
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.backend_base import InferenceBackend
from apps.council_app import CouncilOrchestrator

class MockBackend(InferenceBackend):
    async def load_model(self, spec): pass
    async def unload_model(self, spec): pass
    async def generate(self, request):
        return InferenceResult(
            text=f"Mock response for {request.agent_id}",
            raw={},
            usage={"tokens": 100},
            latency_s=0.05
        )

async def test_council_flow():
    # Setup paths
    root = Path(__file__).parent.parent
    registry = RuntimeRegistry(str(root / "configs"))
    scheduler = InferenceScheduler()
    
    orchestrator = CouncilOrchestrator(scheduler, registry)
    
    # Initialize mock pools for models referenced in the team config
    # For this test, we'll just mock 'gemma4-parallel' as used in our registry checks
    def backend_factory(spec): return MockBackend()
    
    await orchestrator.initialize_pools(["gemma4-parallel"], backend_factory)
    
    # Run a deliberation round
    topic = "The biological plausibility of federated LoRA in cortical microcircuits."
    blackboard = await orchestrator.run_deliberation(
        team_id="sde_debate_team", 
        topic=topic,
        rounds=2
    )
    
    print("\n--- Final Blackboard State ---")
    for entry in blackboard.entries:
        print(f"[{entry.sender}] {entry.content}")
    
    assert len(blackboard.entries) == 8 # 4 agents * 2 rounds
    print("\nTier 1 Verification: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_council_flow())
