import asyncio
import logging
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .structs import InferenceRequest, InferenceResult, ModelSpec
from .model_pool import SharedModelPool
from .backend_lmstudio import LMStudioBackend

logger = logging.getLogger("InferenceScheduler")

@dataclass
class ResourceBudget:
    max_kv_tokens: int = 128000
    current_tokens: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def reserve(self, tokens: int):
        async with self._lock:
            if self.current_tokens + tokens > self.max_kv_tokens:
                raise RuntimeError(f"VRAM Token Budget Exceeded: {self.current_tokens + tokens} > {self.max_kv_tokens}")
            self.current_tokens += tokens

    async def release(self, tokens: int):
        async with self._lock:
            self.current_tokens = max(0, self.current_tokens - tokens)

class InferenceScheduler:
    def __init__(self, registry=None, budget: Optional[ResourceBudget] = None, auto_provision: bool = True):
        self.pools: Dict[str, SharedModelPool] = {}
        self.registry = registry
        self.budget = budget or ResourceBudget()
        self.auto_provision = auto_provision
        self._pool_lock = asyncio.Lock()
        self._default_backend = LMStudioBackend()
        self.audit_log_path = "/Users/HN/MLLM/gamma/local/logs/scheduler_audit.jsonl"

    async def register_pool(self, pool: SharedModelPool):
        async with self._pool_lock:
            if pool.spec.key in self.pools:
                return
            self.pools[pool.spec.key] = pool

    async def _auto_provision_pool(self, model_key: str, caller: str = "unknown") -> SharedModelPool:
        if not self.auto_provision:
             raise RuntimeError(f"Model pool for {model_key} missing and auto-provisioning is disabled.")
        if not self.registry:
            raise RuntimeError(f"Cannot auto-provision {model_key}: No registry provided.")
        
        # 1. Registry-gated only
        try:
            spec = self.registry.load_model(model_key)
        except Exception as e:
            raise RuntimeError(f"Cannot auto-provision {model_key}: Not found in registry. Error: {e}")

        logger.info(f"SAFE AUTO-PROVISIONING model pool: {model_key}")
        
        # 2. Pool Creation
        pool = SharedModelPool(spec, backend=self._default_backend)
        
        # 3. Health check / Readiness probe (Cheap version: ensure_loaded)
        try:
            await pool.ensure_loaded()
        except Exception as e:
            raise RuntimeError(f"Auto-provisioning readiness probe failed for {model_key}: {e}")

        # 4. Structured audit record
        audit_record = {
            "event": "POOL_AUTOPROVISIONED",
            "model_key": model_key,
            "backend": "lmstudio",
            "parallel_slots": spec.max_parallel_slots,
            "timestamp": time.time(),
            "caller": caller
        }
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(audit_record) + "\n")

        self.pools[model_key] = pool
        return pool

    async def schedule(self, model_key: str, request: InferenceRequest) -> InferenceResult:
        pool = self.pools.get(model_key)
        if not pool:
            async with self._pool_lock:
                pool = self.pools.get(model_key)
                if not pool:
                    pool = await self._auto_provision_pool(model_key, caller=request.agent_id)

        estimated_tokens = request.generation.get("max_tokens", 512) + 4096 
        await self.budget.reserve(estimated_tokens)

        try:
            return await pool.generate(request)
        finally:
            await self.budget.release(estimated_tokens)

    async def batch_run(self, requests: List[tuple[str, InferenceRequest]]) -> List[InferenceResult]:
        tasks = [self.schedule(model_key, req) for model_key, req in requests]
        return await asyncio.gather(*tasks)
