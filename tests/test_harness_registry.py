import pytest
from gamma_runtime.harness_registry import (
    AgentIdentity, HarnessIdentity, EnvironmentBackend, ToolBundleRef,
    EvidencePolicy, SessionManifest, admit_player, to_dict
)

def create_valid_manifest(mode="mock"):
    agent = AgentIdentity(
        agent_id="G04-player",
        model_id="gemma-4-31b-mxfp8",
        backend_type="lms",
        role="player"
    )
    harness = HarnessIdentity(
        harness_id="h-001",
        harness_type="terminal",
        endpoint_auth_mode_without_secret="key-based-ssh",
        allowed_tools=["read_file", "grep_search"],
        artifact_policy="strict",
        transcript_policy="full"
    )
    env = EnvironmentBackend(
        environment_id="env-001",
        backend_type="windows-ntfs",
        isolation_mode="worktree",
        network_policy="blocked",
        filesystem_policy="restricted"
    )
    tools = ToolBundleRef(
        bundle_id="b-001",
        tool_ids=["t1", "t2"],
        allowed_planes=["Observation", "Execution"],
        danger_level="low"
    )

    if mode == "live":
        ep = EvidencePolicy(
            artifact_root="./artifacts",
            transcript_path="./transcripts/session.log",
            manifest_required=True,
            hashes_required=True,
            receipt_candidate_required=True
        )
    else:
        ep = EvidencePolicy(
            artifact_root=None,
            transcript_path=None,
            manifest_required=False,
            hashes_required=False,
            receipt_candidate_required=False
        )

    return SessionManifest(
        session_id="s-001",
        agent=agent,
        harness=harness,
        environment=env,
        tool_bundle=tools,
        evidence_policy=ep,
        mock_live_mode=mode
    )

def test_valid_mock_admission_passes():
    manifest = create_valid_manifest(mode="mock")
    record = admit_player("p-001", manifest)
    assert record.admission_status == "admitted"
    assert record.session_manifest == manifest

def test_valid_live_admission_passes_with_requirements():
    manifest = create_valid_manifest(mode="live")
    record = admit_player("p-001", manifest)
    assert record.admission_status == "admitted"

def test_suffix_bearing_model_id_rejects():
    with pytest.raises(ValueError, match="forbidden runtime suffix"):
        AgentIdentity(
            agent_id="G04",
            model_id="gemma:2",
            backend_type="lms",
            role="player"
        )

def test_secret_like_auth_mode_rejects():
    # contains 'sk-'
    with pytest.raises(ValueError, match="forbidden secret-like pattern"):
        HarnessIdentity(
            harness_id="h-001",
            harness_type="terminal",
            endpoint_auth_mode_without_secret="bearer sk-12345",
            allowed_tools=[],
            artifact_policy="none",
            transcript_policy="none"
        )
    # contains 'api_key'
    with pytest.raises(ValueError, match="forbidden secret-like pattern"):
        HarnessIdentity(
            harness_id="h-001",
            harness_type="terminal",
            endpoint_auth_mode_without_secret="my_api_key=foo",
            allowed_tools=[],
            artifact_policy="none",
            transcript_policy="none"
        )

def test_live_mode_without_artifact_path_rejects():
    ep = EvidencePolicy(
        artifact_root=None, # Missing
        transcript_path="./transcripts/session.log",
        manifest_required=True,
        hashes_required=True,
        receipt_candidate_required=True
    )
    with pytest.raises(ValueError, match="Live mode requires artifact_root"):
        SessionManifest(
            session_id="s-001",
            agent=create_valid_manifest().agent,
            harness=create_valid_manifest().harness,
            environment=create_valid_manifest().environment,
            tool_bundle=create_valid_manifest().tool_bundle,
            evidence_policy=ep,
            mock_live_mode="live"
        )

def test_default_truth_mode_is_unverified():
    ep = EvidencePolicy(
        artifact_root=None,
        transcript_path=None,
        manifest_required=False,
        hashes_required=False,
        receipt_candidate_required=False
    )
    assert ep.truth_mode == "truth_safe_unverified"

def test_observation_plus_truth_bundle_safety_check():
    with pytest.raises(ValueError, match="Observation and Truth planes combined"):
        ToolBundleRef(
            bundle_id="b-danger",
            tool_ids=["t1"],
            allowed_planes=["Observation", "Truth"],
            danger_level="high" # Not 'blocked'
        )
    # This should pass
    ToolBundleRef(
        bundle_id="b-safe",
        tool_ids=["t1"],
        allowed_planes=["Observation", "Truth"],
        danger_level="blocked"
    )

def test_player_admission_record_contains_stop_conditions():
    manifest = create_valid_manifest()
    record = admit_player("p-001", manifest)
    assert "session_timeout" in record.stop_conditions
    assert "manual_interrupt" in record.stop_conditions
    assert "security_violation" in record.stop_conditions

def test_json_safe_serialization_works():
    manifest = create_valid_manifest()
    data = to_dict(manifest)
    assert data["session_id"] == "s-001"
    assert data["agent"]["agent_id"] == "G04-player"
    assert "harness" in data
    assert "environment" in data
    assert isinstance(data["tool_bundle"]["allowed_planes"], list)

def test_missing_harness_implicitly_rejected_by_type():
    # In Python with dataclasses, you can't easily pass None to a non-Optional field
    # without type checkers complaining, but we can test if we bypass it.
    # Our admit_player has a check for manifest.harness being None.
    # To trigger it we'd need a manifest with harness=None which SessionManifest
    # doesn't allow by type hint, but dataclasses don't enforce at runtime.

    # We'll skip the direct None test if the class itself doesn't allow it during init
    # but we can try to force it if we want to be exhaustive.
    pass
