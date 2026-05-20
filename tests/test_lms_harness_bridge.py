import pytest
from gamma_runtime.lms_interface import LMSProviderSpec, LMSModelSpec
from gamma_runtime.lms_harness_bridge import admit_lms_player, build_lms_session_manifest
from gamma_runtime.harness_registry import SessionManifest, PlayerAdmissionRecord

@pytest.fixture
def mock_provider():
    return LMSProviderSpec(
        provider_id="mock_provider",
        role="test_role",
        base_url="http://localhost:1234",
        route_ready=True
    )

@pytest.fixture
def mock_model():
    return LMSModelSpec(
        model_id="mock-model-v1",
        model_family="mock_family",
        model_label="Mock Model V1",
        route_ready=True
    )

def test_mock_lms_player_admission_success(mock_provider, mock_model):
    record = admit_lms_player(
        session_id="session_001",
        player_id="player_001",
        model_spec=mock_model,
        provider_spec=mock_provider,
        mock_live_mode="mock"
    )
    assert record.admission_status == "admitted"
    assert record.session_manifest.agent.model_id == "mock-model-v1"
    assert record.session_manifest.mock_live_mode == "mock"

def test_blocked_model_rejects_admission(mock_provider, mock_model):
    blocked_model = LMSModelSpec(
        model_id="blocked-model",
        model_family="blocked",
        model_label="Blocked Model",
        route_ready=False,
        route_block_reason="security_veto"
    )
    record = admit_lms_player(
        session_id="session_001",
        player_id="player_001",
        model_spec=blocked_model,
        provider_spec=mock_provider
    )
    assert record.admission_status == "rejected"
    assert "security_veto" in record.rejection_reasons[0]

def test_blocked_provider_rejects_admission(mock_provider, mock_model):
    blocked_provider = LMSProviderSpec(
        provider_id="blocked_provider",
        role="test",
        route_ready=False,
        route_block_reason="provider_offline"
    )
    record = admit_lms_player(
        session_id="session_001",
        player_id="player_001",
        model_spec=mock_model,
        provider_spec=blocked_provider
    )
    assert record.admission_status == "rejected"
    assert "provider_offline" in record.rejection_reasons[0]

def test_live_admission_without_artifact_root_rejects(mock_provider, mock_model):
    record = admit_lms_player(
        session_id="session_001",
        player_id="player_001",
        model_spec=mock_model,
        provider_spec=mock_provider,
        mock_live_mode="live"
    )
    assert record.admission_status == "rejected"
    assert "Live mode requires artifact_root" in record.rejection_reasons[0]

def test_live_admission_with_required_fields_accepts(mock_provider, mock_model):
    record = admit_lms_player(
        session_id="session_001",
        player_id="player_001",
        model_spec=mock_model,
        provider_spec=mock_provider,
        mock_live_mode="live",
        artifact_root="/tmp/artifacts",
        transcript_path="/tmp/transcript.jsonl"
    )
    assert record.admission_status == "admitted"
    assert record.session_manifest.evidence_policy.artifact_root == "/tmp/artifacts"

def test_truth_mode_remains_unverified(mock_provider, mock_model):
    manifest = build_lms_session_manifest(
        session_id="session_001",
        player_id="player_001",
        model_spec=mock_model,
        provider_spec=mock_provider
    )
    assert manifest.evidence_policy.truth_mode == "truth_safe_unverified"

def test_serialization_does_not_leak_secrets(mock_provider, mock_model):
    # Even if auth_mode is set to something that resolve_session_token_presence
    # uses, we want to ensure the serialized manifest doesn't have secrets.
    # HarnessRegistry already has a check for secret patterns in auth mode.

    # Simulate a provider with a "secret" in auth_mode (should be caught by registry contract)
    risky_provider = LMSProviderSpec(
        provider_id="risky",
        role="test",
        auth_mode="sk-12345", # Forbidden pattern
        route_ready=True
    )

    record = admit_lms_player(
        session_id="session_001",
        player_id="player_001",
        model_spec=mock_model,
        provider_spec=risky_provider
    )
    assert record.admission_status == "rejected"
    assert "forbidden secret-like pattern" in record.rejection_reasons[0]
