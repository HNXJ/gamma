import os

import pytest

from gamma_runtime.lms_interface import (
    LMSCompletionRequest,
    LMSInterface,
    LMSRouteBlockedError,
    build_default_lms_provider,
    resolve_session_token_presence,
)


def test_default_provider_is_truth_safe_and_route_blocked(monkeypatch):
    monkeypatch.delenv("GAMMA_LMS_BASE_URL", raising=False)
    provider = build_default_lms_provider()
    assert provider.truth_status == "truth_safe_unverified"
    assert provider.route_ready is False
    assert provider.route_block_reason == "provider_baseline_not_verified"
    assert len(provider.models) == 2
    assert {model.model_family for model in provider.models} == {"gemma_31b_core", "gemma_26b_agent"}
    assert all(model.route_ready is False for model in provider.models)
    assert all(model.max_concurrent == 8 for model in provider.models)


def test_dry_run_completion_does_not_route_live_model():
    interface = LMSInterface([build_default_lms_provider()])
    response = interface.complete(
        LMSCompletionRequest(
            provider_id="gamma_lms_default",
            model_id="gemma-4-31b-mxfp8",
            messages=[{"role": "user", "content": "ping"}],
            dry_run=True,
        )
    )
    assert response.success is True
    assert response.dry_run is True
    assert response.truth_status == "truth_safe_unverified"
    assert "DRY RUN" in response.content


def test_live_completion_fails_closed_when_provider_not_verified():
    interface = LMSInterface([build_default_lms_provider()])
    with pytest.raises(LMSRouteBlockedError):
        interface.complete(
            LMSCompletionRequest(
                provider_id="gamma_lms_default",
                model_id="gemma-4-31b-mxfp8",
                messages=[{"role": "user", "content": "ping"}],
                dry_run=False,
            )
        )


def test_truth_mutation_request_rejected_even_in_dry_run():
    interface = LMSInterface([build_default_lms_provider()])
    with pytest.raises(LMSRouteBlockedError):
        interface.complete(
            LMSCompletionRequest(
                provider_id="gamma_lms_default",
                model_id="gemma-4-31b-mxfp8",
                messages=[{"role": "user", "content": "ping"}],
                dry_run=True,
                truth_mutation_requested=True,
            )
        )


def test_token_presence_does_not_expose_value(monkeypatch):
    monkeypatch.setenv("LM_STUDIO_API_KEY", "secret-value-not-to-be-returned")
    result = resolve_session_token_presence()
    assert result == {"token_present": True, "env_var_used": "LM_STUDIO_API_KEY"}
    assert "secret-value-not-to-be-returned" not in str(result)
