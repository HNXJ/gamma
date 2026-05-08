import argparse
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LMSProvider:
    provider_id: str
    role: str
    base_url: str
    model_id: Optional[str] = None
    api_style: str = "openai_compatible"
    auth_mode: str = "session_env_only"
    sdk_preferred: bool = True
    truth_mode: str = "truth_safe_unverified"
    truth_bearing_run: bool = False
    timeout_seconds: int = 30


OFFICE_MAC_LMS_PLAYERS = LMSProvider(
    provider_id="office_mac_lms_players",
    role="remote_player_model_host",
    base_url="http://100.69.184.42:1234/v1",
    model_id="gemma-4-e4b-it-mxfp8",
)


def with_model_override(provider: LMSProvider, model_id: str) -> LMSProvider:
    """Return a new LMSProvider instance with an overridden model_id."""
    return LMSProvider(
        provider_id=provider.provider_id,
        role=provider.role,
        base_url=provider.base_url,
        model_id=model_id,
        api_style=provider.api_style,
        auth_mode=provider.auth_mode,
        sdk_preferred=provider.sdk_preferred,
        truth_mode=provider.truth_mode,
        truth_bearing_run=provider.truth_bearing_run,
        timeout_seconds=provider.timeout_seconds,
    )


WINDOWS_LMS_GUARD_JUDGE = LMSProvider(
    provider_id="windows_lms_guard_judge",
    role="guard_judge_receptionist_debugger",
    base_url="http://100.65.139.39:1235/v1",
    model_id="gemma-4-e4b-it-win",
)


def check_lmstudio_sdk_available() -> bool:
    """Return whether lmstudio-python is importable. The bridge must work without it."""
    try:
        import lmstudio  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


def resolve_session_token(env_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Report session-token presence without exposing token values."""
    names = env_names or ["LM_STUDIO_API_KEY", "LMS_API_TOKEN", "LM_API_TOKEN"]
    for name in names:
        if os.environ.get(name):
            return {"token_present": True, "env_var_used": name}
    return {"token_present": False, "env_var_used": None}


def _session_token_value(env_names: Optional[List[str]] = None) -> Optional[str]:
    """Internal-only token lookup. Never print or return this from public results."""
    names = env_names or ["LM_STUDIO_API_KEY", "LMS_API_TOKEN", "LM_API_TOKEN"]
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _request_json(provider: LMSProvider, path: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    token = _session_token_value()
    if token:
        headers["Authorization"] = "Bearer " + token

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    url = provider.base_url.rstrip("/") + path
    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=provider.timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": response.status, "json": json.loads(raw)}
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "error_class": "HTTPError",
            "error_summary": f"HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "error_class": type(exc).__name__,
            "error_summary": str(exc)[:160],
        }


def classify_provider_role(provider: LMSProvider) -> Dict[str, Any]:
    if provider.provider_id == "windows_lms_guard_judge":
        return {
            "allowed_role": "guard_judge_receptionist_debugger",
            "normal_player_backend": False,
            "truth_authority": False,
            "structured_output_required": True,
        }
    if provider.provider_id == "office_mac_lms_players":
        return {
            "allowed_role": "remote_player_model_host",
            "normal_player_backend": True,
            "truth_authority": False,
            "structured_output_required": False,
        }
    return {
        "allowed_role": provider.role,
        "normal_player_backend": False,
        "truth_authority": False,
        "structured_output_required": False,
    }


def list_models_http(provider: LMSProvider) -> Dict[str, Any]:
    result = _request_json(provider, "/models")

    base = {
        "provider_id": provider.provider_id,
        "role": provider.role,
        "transport": "openai_compatible_http_fallback",
        "sdk_available": check_lmstudio_sdk_available(),
        "auth_mode": provider.auth_mode,
        "token_present": resolve_session_token()["token_present"],
        "truth_mode": provider.truth_mode,
        "truth_bearing_run": provider.truth_bearing_run,
    }

    if not result["ok"]:
        return {**base, "success": False, "status": result["status"], "error_class": result["error_class"], "error_summary": result["error_summary"]}

    models = result["json"].get("data", [])
    model_ids = [m.get("id") for m in models if isinstance(m, dict) and m.get("id")]
    target = provider.model_id

    return {
        **base,
        "success": True,
        "status": result["status"],
        "model_count": len(model_ids),
        "target_model_id": target,
        "target_model_present": target in model_ids if target else None,
        "selected_model_id": target if target in model_ids else (model_ids[0] if model_ids else None),
    }


def smoke_chat_http(provider: LMSProvider, prompt: str, max_tokens: int = 160) -> Dict[str, Any]:
    payload = {
        "model": provider.model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
    }
    result = _request_json(provider, "/chat/completions", method="POST", payload=payload)

    base = {
        "provider_id": provider.provider_id,
        "role": provider.role,
        "transport": "openai_compatible_http_fallback",
        "sdk_available": check_lmstudio_sdk_available(),
        "auth_mode": provider.auth_mode,
        "token_present": resolve_session_token()["token_present"],
        "truth_mode": provider.truth_mode,
        "truth_bearing_run": provider.truth_bearing_run,
    }

    if not result["ok"]:
        return {**base, "success": False, "status": result["status"], "error_class": result["error_class"], "error_summary": result["error_summary"]}

    payload_json = result["json"]
    return {
        **base,
        "success": True,
        "status": result["status"],
        "response_keys": sorted(payload_json.keys()),
        "choice_count": len(payload_json.get("choices", [])),
        "model": payload_json.get("model"),
    }


def lms_bridge_heartbeat(session_dir: str) -> Dict[str, Any]:
    """Perform a heartbeat check of all configured LMS providers and log the result."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    hb_file = os.path.join(session_dir, "lms_heartbeat.jsonl")

    results = []
    for name, provider in [("office_mac", OFFICE_MAC_LMS_PLAYERS), ("windows_guard", WINDOWS_LMS_GUARD_JUDGE)]:
        try:
            status = list_models_http(provider)
            results.append({
                "timestamp": timestamp,
                "provider_label": name,
                "provider_id": provider.provider_id,
                "base_url": provider.base_url,
                "success": status.get("success", False),
                "model_count": status.get("model_count", 0),
                "target_model_present": status.get("target_model_present"),
                "adapter_policy": {
                    "enabled": False,
                    "future_supported": ["lora", "dora", "fedlora"],
                    "truth_bearing": False,
                    "rollback_required": True
                }
            })
        except Exception as e:
            results.append({
                "timestamp": timestamp,
                "provider_label": name,
                "error": str(e)
            })

    with open(hb_file, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    return {"status": "OK", "timestamp": timestamp, "provider_count": len(results)}


from datetime import datetime

def provider_from_arg(name: str) -> LMSProvider:
    if name == "office_mac":
        return OFFICE_MAC_LMS_PLAYERS
    if name == "windows_guard":
        return WINDOWS_LMS_GUARD_JUDGE
    raise ValueError(f"unknown provider: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Gamma LMS bridge: SDK-aware, HTTP-fallback, truth-safe smoke utilities.")
    parser.add_argument("--provider", choices=["office_mac", "windows_guard"], required=True)
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--smoke-guard", action="store_true")
    parser.add_argument("--model-id", help="Override provider target model ID")
    args = parser.parse_args()

    provider = provider_from_arg(args.provider)
    if args.model_id:
        provider = with_model_override(provider, args.model_id)

    header = {
        "provider_id": provider.provider_id,
        "role": provider.role,
        "sdk_available": check_lmstudio_sdk_available(),
        "transport_preferred": "lmstudio_sdk_if_available" if provider.sdk_preferred else "openai_compatible_http_fallback",
        "auth_mode": provider.auth_mode,
        "token_present": resolve_session_token()["token_present"],
        "truth_mode": provider.truth_mode,
        "truth_bearing_run": provider.truth_bearing_run,
        "role_constraints": classify_provider_role(provider),
    }
    print(json.dumps(header, indent=2))

    if args.list_models:
        print(json.dumps(list_models_http(provider), indent=2))

    if args.smoke_guard:
        if provider.provider_id != "windows_lms_guard_judge":
            print(json.dumps({"success": False, "error_summary": "--smoke-guard is restricted to windows_lms_guard_judge"}, indent=2))
            return 2
        prompt = "Classify this test envelope: no secrets, no science truth, no player run. Return compact JSON with decision, drift_flags, truth_bearing, and next_action."
        print(json.dumps(smoke_chat_http(provider, prompt), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
