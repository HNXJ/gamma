import time
import httpx
from .types import ModelSpec, InferenceRequest, InferenceResult
from .backend_base import InferenceBackend

class LMStudioBackend(InferenceBackend):
    def __init__(self, base_url: str = "http://127.0.0.1:1234"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def load_model(self, spec: ModelSpec):
        payload = {
            "model": spec.key,
            "context_length": spec.context_length,
            "parallel": spec.max_parallel_slots,
            "echo_load_config": True,
        }
        resp = await self.client.post(f"{self.base_url}/api/v1/models/load", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def unload_model(self, spec: ModelSpec):
        resp = await self.client.post(
            f"{self.base_url}/api/v1/models/unload",
            json={"instance_id": spec.key},
        )
        resp.raise_for_status()
        return resp.json()

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        t0 = time.perf_counter()
        payload = {
            "model": request.model_key,
            "messages": request.messages,
            "stream": False,
            **request.generation,
        }
        resp = await self.client.post(f"{self.base_url}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return InferenceResult(
            text=data["choices"][0]["message"]["content"],
            raw=data,
            usage=data.get("usage", {}),
            latency_s=time.perf_counter() - t0,
        )
