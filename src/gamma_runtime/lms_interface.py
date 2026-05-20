"""Truth-safe LMS interface for Gamma runtime.

This module centralizes model-serving/LMS transport contracts in the `gamma`
Execution-plane repo. It deliberately does not own game controls, judge logic, or
Truth-plane mutation. Live calls are opt-in and fail closed when model/provider
readiness is not explicitly verified.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

TRUTH_SAFE_UNVERIFIED = "truth_safe_unverified"
DEFAULT_TOKEN_ENV_NAMES = ("LM_STUDIO_API_KEY", "LMS_API_TOKEN", "LM_API_TOKEN")


class LMSInterfaceError(RuntimeError):
    """Base class for LMS interface failures."""


class LMSRouteBlockedError(LMSInterfaceError):
    """Raised when a request would route through an unverified model/provider."""


class LMSProviderUnavailableError(LMSInterfaceError):
    """Raised when a live LMS provider is missing or unreachable."""


@dataclass(frozen=True)
class LMSModelSpec:
    """A routeable model identity with explicit readiness state."""

    model_id: str
    model_family: str
    model_label: str
    route_ready: bool = False
    route_block_reason: str = "baseline_load_not_verified"
    max_concurrent: int = 1
    truth_status: str = TRUTH_SAFE_UNVERIFIED

    def require_route_ready(self) -> None:
        if not self.route_ready:
            raise LMSRouteBlockedError(
                f"Model {self.model_id!r} is not route-ready: {self.route_block_reason}"
            )


@dataclass(frozen=True)
class LMSProviderSpec:
    """An LMS/OpenAI-compatible provider contract.

    `base_url` may be omitted for dry-run and capability declaration. When live
    calls are requested, a provider must have `base_url` and `route_ready=True`.
    """

    provider_id: str
    role: str
    base_url: Optional[str] = None
    auth_mode: str = "session_env_only"
    route_ready: bool = False
    route_block_reason: str = "provider_not_verified"
    timeout_seconds: int = 30
    truth_status: str = TRUTH_SAFE_UNVERIFIED
    models: List[LMSModelSpec] = field(default_factory=list)

    def require_route_ready(self) -> None:
        if not self.route_ready:
            raise LMSRouteBlockedError(
                f"Provider {self.provider_id!r} is not route-ready: {self.route_block_reason}"
            )
        if not self.base_url:
            raise LMSProviderUnavailableError(
                f"Provider {self.provider_id!r} has no configured base_url."
            )


@dataclass(frozen=True)
class LMSCompletionRequest:
    provider_id: str
    model_id: str
    messages: List[Mapping[str, str]]
    temperature: float = 0.0
    max_tokens: int = 256
    stream: bool = False
    dry_run: bool = True
    truth_status: str = TRUTH_SAFE_UNVERIFIED
    truth_mutation_requested: bool = False


@dataclass(frozen=True)
class LMSCompletionResponse:
    success: bool
    provider_id: str
    model_id: str
    dry_run: bool
    content: str = ""
    status: Optional[int] = None
    error_class: Optional[str] = None
    error_summary: Optional[str] = None
    token_present: bool = False
    truth_status: str = TRUTH_SAFE_UNVERIFIED
    truth_bearing_run: bool = False


def resolve_session_token_presence(
    env_names: Iterable[str] = DEFAULT_TOKEN_ENV_NAMES,
) -> Dict[str, Any]:
    """Report token presence without exposing secret values."""

    for name in env_names:
        if os.environ.get(name):
            return {"token_present": True, "env_var_used": name}
    return {"token_present": False, "env_var_used": None}


def _session_token_value(env_names: Iterable[str] = DEFAULT_TOKEN_ENV_NAMES) -> Optional[str]:
    for name in env_names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def build_default_lms_provider() -> LMSProviderSpec:
    """Build the default Gamma LMS provider contract from environment.

    The default is intentionally route-blocked. Verification of provider reach,
    model loading, text-only/no-vision mode, and concurrency must happen in a
    separate evidence-bearing task before `route_ready=True` is allowed.
    """

    base_url = os.environ.get("GAMMA_LMS_BASE_URL")
    return LMSProviderSpec(
        provider_id="gamma_lms_default",
        role="remote_player_model_host",
        base_url=base_url.rstrip("/") if base_url else None,
        route_ready=False,
        route_block_reason="provider_baseline_not_verified",
        models=[
            LMSModelSpec(
                model_id="gemma-4-31b-mxfp8",
                model_family="gemma_31b_core",
                model_label="Gemma-31B-Core",
                route_ready=False,
                route_block_reason="baseline_load_not_verified",
                max_concurrent=8,
            ),
            LMSModelSpec(
                model_id="gemma-4-a26b-mxfp8",
                model_family="gemma_26b_agent",
                model_label="Gemma-26B-Agent",
                route_ready=False,
                route_block_reason="baseline_load_not_verified",
                max_concurrent=8,
            ),
        ],
    )


class LMSInterface:
    """Truth-safe OpenAI-compatible LMS transport wrapper."""

    def __init__(self, providers: Optional[Iterable[LMSProviderSpec]] = None):
        provider_list = list(providers) if providers is not None else [build_default_lms_provider()]
        self.providers: Dict[str, LMSProviderSpec] = {p.provider_id: p for p in provider_list}

    def provider(self, provider_id: str) -> LMSProviderSpec:
        try:
            return self.providers[provider_id]
        except KeyError as exc:
            raise LMSProviderUnavailableError(f"Unknown LMS provider: {provider_id}") from exc

    def model(self, provider_id: str, model_id: str) -> LMSModelSpec:
        provider = self.provider(provider_id)
        for model in provider.models:
            if model.model_id == model_id:
                return model
        raise LMSRouteBlockedError(f"Unknown model {model_id!r} for provider {provider_id!r}")

    def capability_manifest(self) -> Dict[str, Any]:
        return {
            "truth_status": TRUTH_SAFE_UNVERIFIED,
            "truth_bearing_run": False,
            "providers": [asdict(provider) for provider in self.providers.values()],
            "token": resolve_session_token_presence(),
        }

    def list_models(self, provider_id: str, dry_run: bool = True) -> Dict[str, Any]:
        provider = self.provider(provider_id)
        base = {
            "provider_id": provider.provider_id,
            "role": provider.role,
            "dry_run": dry_run,
            "truth_status": TRUTH_SAFE_UNVERIFIED,
            "truth_bearing_run": False,
            "token_present": resolve_session_token_presence()["token_present"],
        }
        if dry_run:
            return {
                **base,
                "success": True,
                "source": "configured_capability_manifest",
                "models": [asdict(model) for model in provider.models],
            }

        provider.require_route_ready()
        return self._request_json(provider, "/models") | base

    def complete(self, request: LMSCompletionRequest) -> LMSCompletionResponse:
        provider = self.provider(request.provider_id)
        model = self.model(request.provider_id, request.model_id)
        token_present = resolve_session_token_presence()["token_present"]

        if request.truth_mutation_requested:
            raise LMSRouteBlockedError("LMS requests may not request Truth-plane mutation.")

        if request.dry_run:
            return LMSCompletionResponse(
                success=True,
                provider_id=provider.provider_id,
                model_id=model.model_id,
                dry_run=True,
                content="[DRY RUN] LMS completion bypassed; no model inference executed.",
                token_present=token_present,
            )

        provider.require_route_ready()
        model.require_route_ready()
        payload = {
            "model": request.model_id,
            "messages": list(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
        }
        result = self._request_json(provider, "/chat/completions", method="POST", payload=payload)
        if not result.get("ok"):
            return LMSCompletionResponse(
                success=False,
                provider_id=provider.provider_id,
                model_id=model.model_id,
                dry_run=False,
                status=result.get("status"),
                error_class=result.get("error_class"),
                error_summary=result.get("error_summary"),
                token_present=token_present,
            )
        body = result.get("json", {})
        choices = body.get("choices", []) if isinstance(body, dict) else []
        content = ""
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                content = str(message.get("content", ""))
        return LMSCompletionResponse(
            success=True,
            provider_id=provider.provider_id,
            model_id=model.model_id,
            dry_run=False,
            content=content,
            status=result.get("status"),
            token_present=token_present,
        )

    def _request_json(
        self,
        provider: LMSProviderSpec,
        path: str,
        method: str = "GET",
        payload: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        token = _session_token_value()
        if token:
            headers["Authorization"] = "Bearer " + token
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            provider.base_url.rstrip("/") + path,  # type: ignore[union-attr]
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=provider.timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return {"ok": True, "status": response.status, "json": json.loads(raw)}
        except urllib.error.HTTPError as exc:
            return {"ok": False, "status": exc.code, "error_class": "HTTPError", "error_summary": f"HTTP {exc.code}"}
        except Exception as exc:  # pragma: no cover - network environment dependent
            return {"ok": False, "status": None, "error_class": type(exc).__name__, "error_summary": str(exc)[:160]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Gamma truth-safe LMS interface")
    parser.add_argument("--provider", default="gamma_lms_default")
    parser.add_argument("--model", default="gemma-4-31b-mxfp8")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--capabilities", action="store_true")
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--prompt", default="Return compact JSON acknowledging dry-run LMS interface.")
    parser.add_argument("--live", action="store_true", help="Attempt live route; fails closed unless provider/model are route-ready.")
    args = parser.parse_args()

    interface = LMSInterface()
    if args.capabilities:
        print(json.dumps(interface.capability_manifest(), indent=2))
    if args.list_models:
        print(json.dumps(interface.list_models(args.provider, dry_run=not args.live), indent=2))
    if args.complete:
        response = interface.complete(
            LMSCompletionRequest(
                provider_id=args.provider,
                model_id=args.model,
                messages=[{"role": "user", "content": args.prompt}],
                dry_run=not args.live,
            )
        )
        print(json.dumps(asdict(response), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
