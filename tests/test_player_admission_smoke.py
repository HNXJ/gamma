import pytest
import json
from gamma_runtime.lms_interface import LMSProviderSpec, LMSModelSpec
from gamma_runtime.lms_harness_bridge import admit_lms_player
from gamma_runtime.harness_registry import to_dict

@pytest.fixture
def route_ready_provider():
    return LMSProviderSpec(
        provider_id="gamma_lms_test",
        role="remote_player_model_host",
        base_url="http://localhost:11434",
        route_ready=True
    )

@pytest.fixture
def route_ready_model():
    return LMSModelSpec(
        model_id="gemma-4-31b-mxfp8",
        model_family="gemma_31b_core",
        model_label="Gemma-31B-Core",
        route_ready=True
    )

def test_mock_lms_player_admission_end_to_end_passes(route_ready_provider, route_ready_model):
    """Confirm a mock LMS-backed player can be admitted end-to-end."""

    player_id = "player_test_01"
    session_id = "session_test_01"

    record = admit_lms_player(
        session_id=session_id,
        player_id=player_id,
        model_spec=route_ready_model,
        provider_spec=route_ready_provider,
        mock_live_mode="mock"
    )

    # Assertions
    assert record.admission_status == "admitted"
    assert record.player_id == player_id

    manifest = record.session_manifest
    assert manifest is not None
    assert manifest.session_id == session_id

    # Agent Identity
    assert manifest.agent.agent_id == player_id
    assert manifest.agent.model_id == "gemma-4-31b-mxfp8"
    assert ":" not in manifest.agent.model_id  # Ensure no runtime suffix

    # Harness Identity
    assert manifest.harness.harness_type == "lms_gateway"
    assert "token_present=" in manifest.harness.endpoint_auth_mode_without_secret

    # Tool Bundle (Plane Separation)
    assert "Truth" not in manifest.tool_bundle.allowed_planes
    assert manifest.tool_bundle.danger_level == "safe"

    # Evidence Policy (Truth Mode)
    assert manifest.evidence_policy.truth_mode == "truth_safe_unverified"
    assert manifest.evidence_policy.claim_type == "runtime_admission_candidate"

    # Mock/Live Mode
    assert manifest.mock_live_mode == "mock"

    # Stop Conditions
    assert "session_timeout" in record.stop_conditions

    # JSON-safe serialization
    d = to_dict(record)
    json_str = json.dumps(d)
    assert isinstance(json_str, str)

def test_blocked_model_lms_player_admission_rejects(route_ready_provider):
    """Confirm admission is rejected if the model is not route-ready."""

    blocked_model = LMSModelSpec(
        model_id="blocked-model",
        model_family="unverified",
        model_label="Blocked Model",
        route_ready=False,
        route_block_reason="baseline_load_not_verified"
    )

    record = admit_lms_player(
        session_id="session_test_01",
        player_id="player_test_01",
        model_spec=blocked_model,
        provider_spec=route_ready_provider
    )

    assert record.admission_status == "rejected"
    assert record.session_manifest is None
    assert any("baseline_load_not_verified" in r for r in record.rejection_reasons)

def test_live_lms_player_admission_requires_artifacts(route_ready_provider, route_ready_model):
    """Confirm live mode requires evidence paths."""

    # 1. Rejects without artifact_root
    record_fail = admit_lms_player(
        session_id="session_test_01",
        player_id="player_test_01",
        model_spec=route_ready_model,
        provider_spec=route_ready_provider,
        mock_live_mode="live"
    )
    assert record_fail.admission_status == "rejected"
    assert any("requires artifact_root" in r for r in record_fail.rejection_reasons)

    # 2. Accepts with artifacts (metadata only, no runtime started)
    record_pass = admit_lms_player(
        session_id="session_test_01",
        player_id="player_test_01",
        model_spec=route_ready_model,
        provider_spec=route_ready_provider,
        mock_live_mode="live",
        artifact_root="runtime_artifacts/test_session",
        transcript_path="runtime_artifacts/test_session/transcript.jsonl"
    )
    assert record_pass.admission_status == "admitted"
    assert record_pass.session_manifest.mock_live_mode == "live"
    assert record_pass.session_manifest.evidence_policy.manifest_required is True
    assert record_pass.session_manifest.evidence_policy.hashes_required is True
