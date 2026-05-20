"""Adapter bridge between Harness Registry and LMS Interface.

This module allows converting LMS provider/model specifications into
formal Harness Registry contracts (SessionManifest, PlayerAdmissionRecord).
"""

from typing import List, Optional, Any, Dict
from .harness_registry import (
    AgentIdentity,
    HarnessIdentity,
    EnvironmentBackend,
    ToolBundleRef,
    EvidencePolicy,
    SessionManifest,
    PlayerAdmissionRecord,
    admit_player
)
from .lms_interface import LMSProviderSpec, LMSModelSpec, resolve_session_token_presence

def build_lms_session_manifest(
    session_id: str,
    player_id: str,
    model_spec: LMSModelSpec,
    provider_spec: LMSProviderSpec,
    mock_live_mode: str = "mock",
    artifact_root: Optional[str] = None,
    transcript_path: Optional[str] = None,
    tool_ids: Optional[List[str]] = None,
    environment_id: str = "default_lms_env"
) -> SessionManifest:
    """Build a formal SessionManifest from LMS specs."""

    # 1. Agent Identity
    agent = AgentIdentity(
        agent_id=player_id,
        model_id=model_spec.model_id,
        backend_type="lms",
        role=provider_spec.role,
        display_name=model_spec.model_label
    )

    # 2. Harness Identity
    # Use resolve_session_token_presence to get safe auth info
    token_info = resolve_session_token_presence()
    auth_mode = f"{provider_spec.auth_mode} (token_present={token_info['token_present']})"

    harness = HarnessIdentity(
        harness_id=f"harness_{session_id}",
        harness_type="lms_gateway",
        endpoint_auth_mode_without_secret=auth_mode,
        allowed_tools=tool_ids or [],
        artifact_policy="strict_ignore",
        transcript_policy="jsonl_buffered"
    )

    # 3. Environment Backend
    env = EnvironmentBackend(
        environment_id=environment_id,
        backend_type="lms_isolated",
        isolation_mode="container" if mock_live_mode == "live" else "process",
        network_policy="restricted_lms_only",
        filesystem_policy="ephemeral_only"
    )

    # 4. Tool Bundle
    tool_bundle = ToolBundleRef(
        bundle_id=f"tools_{session_id}",
        tool_ids=tool_ids or [],
        allowed_planes=["Execution", "Observation"],
        danger_level="safe"
    )

    # 5. Evidence Policy
    evidence_policy = EvidencePolicy(
        artifact_root=artifact_root,
        transcript_path=transcript_path,
        manifest_required=(mock_live_mode == "live"),
        hashes_required=(mock_live_mode == "live"),
        receipt_candidate_required=True,
        truth_mode="truth_safe_unverified",
        claim_type="runtime_admission_candidate"
    )

    return SessionManifest(
        session_id=session_id,
        agent=agent,
        harness=harness,
        environment=env,
        tool_bundle=tool_bundle,
        evidence_policy=evidence_policy,
        mock_live_mode=mock_live_mode
    )

def admit_lms_player(
    session_id: str,
    player_id: str,
    model_spec: LMSModelSpec,
    provider_spec: LMSProviderSpec,
    mock_live_mode: str = "mock",
    artifact_root: Optional[str] = None,
    transcript_path: Optional[str] = None,
    tool_ids: Optional[List[str]] = None
) -> PlayerAdmissionRecord:
    """Admit an LMS player with fail-closed route validation."""

    rejection_reasons = []

    # Fail-closed: check route readiness
    if not provider_spec.route_ready:
        rejection_reasons.append(f"Provider '{provider_spec.provider_id}' not route-ready: {provider_spec.route_block_reason}")

    if not model_spec.route_ready:
        rejection_reasons.append(f"Model '{model_spec.model_id}' not route-ready: {model_spec.route_block_reason}")

    # If route is blocked, we don't even try to build the manifest to avoid side effects
    if rejection_reasons:
        return PlayerAdmissionRecord(
            player_id=player_id,
            session_manifest=None,
            admission_status="rejected",
            rejection_reasons=rejection_reasons,
            stop_conditions=["route_blocked"]
        )

    try:
        manifest = build_lms_session_manifest(
            session_id=session_id,
            player_id=player_id,
            model_spec=model_spec,
            provider_spec=provider_spec,
            mock_live_mode=mock_live_mode,
            artifact_root=artifact_root,
            transcript_path=transcript_path,
            tool_ids=tool_ids
        )
        return admit_player(player_id, manifest)
    except Exception as e:
        return PlayerAdmissionRecord(
            player_id=player_id,
            session_manifest=None,
            admission_status="rejected",
            rejection_reasons=[str(e)],
            stop_conditions=["initialization_error"]
        )
