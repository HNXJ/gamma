import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from gamma_runtime.structs import ModelSpec, InferenceRequest
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.scheduler import InferenceScheduler, ResourceBudget
from gamma_runtime.backend_base import InferenceBackend

class MockBackend(InferenceBackend):
    async def load_model(self, spec): pass
    async def unload_model(self, spec): pass
    async def generate(self, request):
        return {"text": "mock success", "raw": {}, "usage": {}, "latency_s": 0.1}

async def test_scheduler():
    spec = ModelSpec(key="test-model", provider="mock", max_parallel_slots=2)
    backend = MockBackend()
    pool = SharedModelPool(spec, backend)
    
    scheduler = InferenceScheduler()
    await scheduler.register_pool(pool)
    
    req = InferenceRequest(
        session_id="test-session",
        agent_id="test-agent",
        model_key="test-model",
        messages=[],
        generation={"max_tokens": 100},
        adapter_stack=[]
    )
    
    print("Testing single schedule...")
    res = await scheduler.schedule("test-model", req)
    print(f"Result: {res}")
    
    print("Testing batch run...")
    results = await scheduler.batch_run([("test-model", req), ("test-model", req)])
    print(f"Batch results count: {len(results)}")
    
    print("Tier 0 Verification: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_scheduler())
