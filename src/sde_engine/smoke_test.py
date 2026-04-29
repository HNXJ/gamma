import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from gamma_runtime.structs import ModelSpec, InferenceResult, AgentSpec
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.backend_base import InferenceBackend
from sde_engine.solver import SDESolver

class MockBackend(InferenceBackend):
    async def load_model(self, spec): pass
    async def unload_model(self, spec): pass
    async def generate(self, request):
        return InferenceResult(
            text=f"Proposal/Critique from {request.agent_id}",
            raw={},
            usage={},
            latency_s=0.1
        )

async def test_sde_engine():
    # Setup Runtime
    scheduler = InferenceScheduler()
    blackboard = Blackboard("Jaxley E-I Optimization")
    
    # Register mock pool
    spec = ModelSpec(key="test-model", provider="mlx", max_parallel_slots=4)
    pool = SharedModelPool(spec, MockBackend())
    await scheduler.register_pool(pool)
    
    # Setup SDE Engine
    solver = SDESolver(scheduler, blackboard)
    
    # Define Mock Agents
    proponent = AgentSpec(
        agent_id="excitatory_specialist",
        role="Proponent",
        model_key="test-model",
        system_prompt="You are an expert in AMPA kinetics."
    )
    
    adversary = AgentSpec(
        agent_id="inhibitory_specialist",
        role="Adversary",
        model_key="test-model",
        system_prompt="You are a skeptical neuroscientist."
    )
    
    print("🚀 Starting SDE Smoke Test...")
    result_entry = await solver.run_optimization_cycle(proponent, adversary)
    
    print("\n--- SDE State committed to Blackboard ---")
    print(f"Metrics: {result_entry.metadata['x']:.2f}, {result_entry.metadata['z']:.2f}")
    print(f"Global Loss: {result_entry.metadata['loss']:.4f}")
    
    assert 'sde_metrics' in result_entry.metadata['kind']
    print("\nSDE Engine Verification: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_sde_engine())
