from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx


class LMStudioError(RuntimeError):
    pass


@dataclass
class LMSLoadConfig:
    model: str
    identifier: Optional[str] = None
    gpu: str = "max"
    context_length: Optional[int] = None
    ttl: Optional[int] = None
    host: Optional[str] = None


@dataclass
class LMSGenerationConfig:
    temperature: float = 0.2
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    seed: Optional[int] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


class LMSHandler:
    def __init__(
        self,
        *,
        lms_bin: str = "lms",
        base_url: str = "http://127.0.0.1:1234",
        api_key: str = "lm-studio",
        timeout_s: float = 600.0,
    ) -> None:
        self.lms_bin = lms_bin
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s

        if shutil.which(self.lms_bin) is None:
            raise LMStudioError(f"Could not find CLI binary: {self.lms_bin}")

        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_s,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        await self._http.aclose()

    def _run_lms(self, args: List[str], *, check: bool = True) -> subprocess.CompletedProcess:
        cmd = [self.lms_bin] + args
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if check and proc.returncode != 0:
            raise LMStudioError(
                f"Command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )
        return proc

    def start_server(self, *, port: Optional[int] = None, cors: bool = False) -> str:
        args = ["server", "start"]
        if port is not None:
            args += ["--port", str(port)]
            self.base_url = f"http://127.0.0.1:{port}"
            self._http.base_url = httpx.URL(self.base_url)
        if cors:
            args += ["--cors"]
        proc = self._run_lms(args)
        return proc.stdout.strip()

    def stop_server(self) -> str:
        proc = self._run_lms(["server", "stop"], check=False)
        return (proc.stdout or proc.stderr).strip()

    def server_status(self, *, json_mode: bool = True, quiet: bool = True) -> str:
        args = ["server", "status"]
        if json_mode:
            args += ["--json"]
        if quiet:
            args += ["--quiet"]
        proc = self._run_lms(args, check=False)
        return (proc.stdout or proc.stderr).strip()

    def list_local_models(self) -> str:
        return self._run_lms(["ls"]).stdout

    def list_loaded_models(self) -> str:
        return self._run_lms(["ps"], check=False).stdout

    def load(self, cfg: LMSLoadConfig) -> str:
        args = ["load", cfg.model]
        if cfg.identifier:
            args += ["--identifier", cfg.identifier]
        if cfg.gpu:
            args += ["--gpu", str(cfg.gpu)]
        if cfg.context_length is not None:
            args += ["--context-length", str(cfg.context_length)]
        if cfg.ttl is not None:
            args += ["--ttl", str(cfg.ttl)]
        if cfg.host:
            args += ["--host", cfg.host]
        proc = self._run_lms(args)
        return proc.stdout.strip()

    def unload(self, model: Optional[str] = None, *, unload_all: bool = False) -> str:
        args = ["unload"]
        if unload_all:
            args += ["--all"]
        elif model:
            args += [model]
        proc = self._run_lms(args, check=False)
        return (proc.stdout or proc.stderr).strip()

    def ensure_loaded(
        self,
        *,
        model: str,
        identifier: Optional[str] = None,
        gpu: str = "max",
        context_length: Optional[int] = None,
        ttl: Optional[int] = None,
        host: Optional[str] = None,
    ) -> str:
        loaded = self.list_loaded_models()
        target = identifier or model
        if target in loaded:
            return target
        self.load(
            LMSLoadConfig(
                model=model,
                identifier=identifier,
                gpu=gpu,
                context_length=context_length,
                ttl=ttl,
                host=host,
            )
        )
        return target

    async def chat_completions(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        generation: Optional[LMSGenerationConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        gen = generation or LMSGenerationConfig()
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": gen.temperature,
            "stream": gen.stream,
        }
        if gen.top_p is not None:
            payload["top_p"] = gen.top_p
        if gen.top_k is not None:
            payload["top_k"] = gen.top_k
        if gen.max_tokens is not None:
            payload["max_tokens"] = gen.max_tokens
        if gen.seed is not None:
            payload["seed"] = gen.seed
        if gen.stop is not None:
            payload["stop"] = gen.stop
        if tools is not None:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            
        payload.update(gen.extra)

        r = await self._http.post("/v1/chat/completions", json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LMStudioError(
                f"Chat request failed [{r.status_code}] at {self.base_url}/v1/chat/completions\n"
                f"payload={json.dumps(payload, ensure_ascii=False)}\nbody={r.text}"
            ) from e
        return r.json()
