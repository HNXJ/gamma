import time
import httpx
from .types import ModelSpec, InferenceRequest, InferenceResult
from .backend_base import InferenceBackend
from .config import get_lms_url

class LMStudioBackend(InferenceBackend):
    def __init__(self, base_url: str = None):
        self.base_url = base_url or get_lms_url()
        self.client = httpx.AsyncClient(timeout=120.0)

    async def load_model(self, spec: ModelSpec):
        return {"status": "already_running"}

    async def unload_model(self, spec: ModelSpec):
        resp = await self.client.post(
            f"{self.base_url}/api/v1/models/unload",
            json={"instance_id": spec.key},
        )
        resp.raise_for_status()
        return resp.json()

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        t0 = time.perf_counter()
        
        from .model_router import resolve_lms_identifier
        resolved_model = resolve_lms_identifier(request.agent_id, request.model_key)
        
        payload = {
            "model": resolved_model,
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
