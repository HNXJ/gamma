import asyncio
import logging
from typing import Any
from .types import ModelSpec, PoolStats

class SharedModelPool:
    def __init__(self, spec: ModelSpec, backend):
        self.spec = spec
        self.backend = backend
        self._loaded = False
        self._load_lock = asyncio.Lock()
        self._sem = asyncio.Semaphore(spec.max_parallel_slots)
        self.stats = PoolStats()

    async def ensure_loaded(self) -> None:
        if self._loaded:
            return
        async with self._load_lock:
            if self._loaded:
                return
            print(f"INFO: Loading shared weights for {self.spec.key} via {self.spec.provider}")
            await self.backend.load_model(self.spec)
            self._loaded = True

    async def generate(self, request) -> Any:
        await self.ensure_loaded()
        async with self._sem:
            self.stats.active_requests += 1
            self.stats.total_requests += 1
            try:
                return await self.backend.generate(request)
            finally:
                self.stats.active_requests -= 1
