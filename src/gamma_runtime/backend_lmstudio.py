import time
import logging
from typing import Any, Dict

from .structs import ModelSpec, InferenceRequest, InferenceResult
from .backend_base import InferenceBackend
from .lms_handler import LMSHandler, LMSGenerationConfig

logger = logging.getLogger("LMStudioBackend")


class LMStudioBackend(InferenceBackend):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234",
        api_key: str = "lm-studio",
        lms_bin: str = "/Users/HN/.lmstudio/bin/lms",
        preload_via_cli: bool = True,
        start_server: bool = False,
    ):
        self.base_url = base_url
        self.preload_via_cli = preload_via_cli
        self.handler = LMSHandler(
            lms_bin=lms_bin,
            base_url=base_url,
            api_key=api_key,
        )
        if start_server:
            try:
                port = int(base_url.rsplit(":", 1)[-1])
            except Exception:
                port = 1234
            self.handler.start_server(port=port)

    def _resolve_model_name(self, spec: ModelSpec) -> str:
        return spec.name or spec.key

    def _resolve_identifier(self, spec: ModelSpec) -> str:
        return spec.config.get("identifier", spec.key) if spec.config else spec.key

    async def load_model(self, spec: ModelSpec):
        model_name = self._resolve_model_name(spec)
        identifier = self._resolve_identifier(spec)
        if not self.preload_via_cli:
            logger.info("Skipping explicit CLI preload for %s; LM Studio may auto-load on first request.", model_name)
            return {"model": model_name, "identifier": identifier, "loaded": False, "mode": "auto"}

        logger.info("Ensuring LM Studio model is loaded via CLI: %s (identifier=%s)", model_name, identifier)
        target = self.handler.ensure_loaded(
            model=model_name,
            identifier=identifier,
            gpu=str(spec.config.get("gpu", "max")) if spec.config else "max",
            context_length=spec.context_length,
            ttl=spec.config.get("ttl") if spec.config else None,
        )
        return {"model": model_name, "identifier": target, "loaded": True, "mode": "cli"}

    async def unload_model(self, spec: ModelSpec):
        identifier = self._resolve_identifier(spec)
        logger.info("Requesting LM Studio unload for %s", identifier)
        msg = self.handler.unload(identifier)
        return {"identifier": identifier, "message": msg}

    async def generate(self, request: InferenceRequest) -> InferenceResult:
        t0 = time.perf_counter()
        gen_cfg = LMSGenerationConfig(
            temperature=request.generation.get("temperature", 0.2),
            top_p=request.generation.get("top_p"),
            top_k=request.generation.get("top_k"),
            max_tokens=request.generation.get("max_tokens", 512),
            seed=request.generation.get("seed"),
            stop=request.generation.get("stop"),
            stream=False,
            extra={
                k: v
                for k, v in request.generation.items()
                if k not in {"temperature", "top_p", "top_k", "max_tokens", "seed", "stop", "stream"}
            },
        )
        data = await self.handler.chat_completions(
            model=request.model_key,
            messages=request.messages,
            generation=gen_cfg,
            tools=request.tools
        )
        t1 = time.perf_counter()
        
        msg = data["choices"][0]["message"]
        return InferenceResult(
            text=msg.get("content") or "",
            raw=data,
            usage=data.get("usage", {}),
            latency_s=t1 - t0,
            tool_calls=msg.get("tool_calls")
        )
