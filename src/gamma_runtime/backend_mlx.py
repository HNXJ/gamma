import time
import httpx
import logging
from .types import ModelSpec, InferenceRequest, InferenceResult
from .backend_base import InferenceBackend
from .config import get_lms_url

logger = logging.getLogger("MLXBackend")

class MLXEngineBackend(InferenceBackend):
    def __init__(self, base_url: str = None, api_key: str = "mlx-server"):
        self.base_url = base_url or get_lms_url()
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(timeout=300.0, headers=self.headers)

    async def load_model(self, spec: ModelSpec):
        logger.info(f"Requesting load for {spec.key} on MLX engine...")
        resp = await self.client.post(f"{self.base_url}/load_model", json={"model": spec.key})
        resp.raise_for_status()
        return resp.json()

    async def unload_model(self, spec: ModelSpec):
        logger.info(f"Requesting unload for {spec.key} on MLX engine...")
        resp = await self.client.post(f"{self.base_url}/unload_all")
        resp.raise_for_status()
        return resp.json()

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        t0 = time.perf_counter()
        payload = {
            "model": request.model_key,
            "messages": request.messages,
            "temperature": request.generation.get("temperature", 0.7),
            "max_tokens": request.generation.get("max_tokens", 2048),
            "min_p": request.generation.get("min_p", 0.1),
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
