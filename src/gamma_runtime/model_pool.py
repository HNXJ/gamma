import asyncio
from dataclasses import dataclass
from .types import ModelSpec, InferenceRequest, InferenceResult
from .backend_base import InferenceBackend

@dataclass
class PoolStats:
    inflight: int = 0
    queued: int = 0
    total_requests: int = 0

class SharedModelPool:
    """Manages base weight residency. Ensures models are loaded exactly once."""
    
    def __init__(self, spec: ModelSpec, backend: InferenceBackend):
        self.spec = spec
        self.backend = backend
        self._loaded = False
        self._sem = asyncio.Semaphore(spec.max_parallel_slots)
        self.stats = PoolStats()

    async def ensure_loaded(self) -> None:
        if not self._loaded:
            print(f"INFO: Loading shared weights for {self.spec.key} via {self.spec.provider}")
            await self.backend.load_model(self.spec)
            self._loaded = True

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        await self.ensure_loaded()
        self.stats.queued += 1
        async with self._sem:
            self.stats.queued -= 1
            self.stats.inflight += 1
            self.stats.total_requests += 1
            try:
                print(f"DEBUG: Executing request {request.session_id} on {self.spec.key}")
                return await self.backend.generate(request)
            finally:
                self.stats.inflight -= 1
