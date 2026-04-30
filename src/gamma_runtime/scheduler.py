import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .types import InferenceRequest, InferenceResult, ModelSpec
from .model_pool import SharedModelPool

@dataclass
class ResourceBudget:
    """Tracks and limits global KV-cache token consumption to prevent Jetsam kills."""
    max_kv_tokens: int = 128000
    current_tokens: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def reserve(self, tokens: int):
        async with self._lock:
            if self.current_tokens + tokens > self.max_kv_tokens:
                # In a production scheduler, this would queue. 
                # For Gamma Phase 2, we fail fast to protect the host.
                raise RuntimeError(f"VRAM Token Budget Exceeded: {self.current_tokens + tokens} > {self.max_kv_tokens}")
            self.current_tokens += tokens

    async def release(self, tokens: int):
        async with self._lock:
            self.current_tokens = max(0, self.current_tokens - tokens)

class InferenceScheduler:
    """
    The orchestrator of the Gamma Runtime.
    Enforces singleton residency via model pools and strict resource budgets.
    """
    def __init__(self, budget: Optional[ResourceBudget] = None):
        self.pools: Dict[str, SharedModelPool] = {}
        self.budget = budget or ResourceBudget()
        self._pool_lock = asyncio.Lock()

    async def register_pool(self, pool: SharedModelPool):
        async with self._pool_lock:
            if pool.spec.key in self.pools:
                return
            self.pools[pool.spec.key] = pool

    async def schedule(self, model_key: str, request: InferenceRequest) -> InferenceResult:
        """
        Entry point for all inference. 
        Routes requests through residency checks and VRAM budgets.
        """
        pool = self.pools.get(model_key)
        if not pool:
            raise RuntimeError(f"Model pool for {model_key} not registered in scheduler.")

        # 1. Budget Reservation (Estimating worst-case KV usage)
        # We assume max_tokens + reasonable prompt context overhead
        estimated_tokens = request.generation.get("max_tokens", 512) + 4096 
        await self.budget.reserve(estimated_tokens)

        try:
            # 2. Pool Execution (Ensures singleton loading + slot semaphore)
            return await pool.generate(request)
        finally:
            # 3. Budget Release
            await self.budget.release(estimated_tokens)

    async def batch_run(self, requests: List[tuple[str, InferenceRequest]]) -> List[InferenceResult]:
        """
        Managed parallel execution. 
        Strictly replaces unmanaged asyncio.gather at the application layer.
        """
        tasks = [self.schedule(model_key, req) for model_key, req in requests]
        return await asyncio.gather(*tasks)
