import dataclasses
import re
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

@dataclasses.dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    model_id: str
    backend_type: str
    role: str
    display_name: Optional[str] = None

    def __post_init__(self):
        # Rule: Reject canonical model_id values containing runtime suffixes like :2, :3
        if re.search(r":\d+$", self.model_id):
            raise ValueError(f"Model ID '{self.model_id}' contains forbidden runtime suffix.")

@dataclasses.dataclass(frozen=True)
class HarnessIdentity:
    harness_id: str
    harness_type: str
    endpoint_auth_mode_without_secret: str
    allowed_tools: List[str]
    artifact_policy: str
    transcript_policy: str

    def __post_init__(self):
        # Rule: Reject secret-like values in auth/endpoint fields.
        forbidden_patterns = [r"sk-", r"token=", r"api_key", r"secret", r"bearer "]
        for pattern in forbidden_patterns:
            if re.search(pattern, self.endpoint_auth_mode_without_secret, re.IGNORECASE):
                # Do not print the value to avoid leakage
                raise ValueError("Auth mode contains forbidden secret-like pattern.")

@dataclasses.dataclass(frozen=True)
class EnvironmentBackend:
    environment_id: str
    backend_type: str
    isolation_mode: str
    network_policy: str
    filesystem_policy: str

@dataclasses.dataclass(frozen=True)
class ToolBundleRef:
    bundle_id: str
    tool_ids: List[str]
    allowed_planes: List[str]
    danger_level: str

    def __post_init__(self):
        # Rule: Observation-plane tools cannot mutate Truth-plane state.
        # Minimal rule: if allowed_planes contains Observation, it must not contain Truth
        # unless danger_level is explicitly blocked.
        if "Observation" in self.allowed_planes and "Truth" in self.allowed_planes:
            if self.danger_level != "blocked":
                raise ValueError("Observation and Truth planes combined without 'blocked' danger level.")

@dataclasses.dataclass(frozen=True)
class EvidencePolicy:
    artifact_root: Optional[str]
    transcript_path: Optional[str]
    manifest_required: bool
    hashes_required: bool
    receipt_candidate_required: bool
    truth_mode: str = "truth_safe_unverified"
    claim_type: str = "observation"

@dataclasses.dataclass(frozen=True)
class SessionManifest:
    session_id: str
    agent: AgentIdentity
    harness: HarnessIdentity
    environment: EnvironmentBackend
    tool_bundle: ToolBundleRef
    evidence_policy: EvidencePolicy
    mock_live_mode: str  # 'mock' or 'live'
    created_at: str = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        # Rule: Reject live mode unless requirements are met
        if self.mock_live_mode == "live":
            ep = self.evidence_policy
            if not ep.artifact_root:
                raise ValueError("Live mode requires artifact_root.")
            if not ep.transcript_path:
                raise ValueError("Live mode requires transcript_path.")
            if not ep.manifest_required:
                raise ValueError("Live mode requires manifest_required=True.")
            if not ep.hashes_required:
                raise ValueError("Live mode requires hashes_required=True.")

@dataclasses.dataclass(frozen=True)
class PlayerAdmissionRecord:
    player_id: str
    session_manifest: Optional[SessionManifest]
    admission_status: str  # 'admitted' or 'rejected'
    rejection_reasons: List[str]
    stop_conditions: List[str]

def admit_player(player_id: str, manifest: SessionManifest) -> PlayerAdmissionRecord:
    rejection_reasons = []

    # 1. Reject missing harness identity (implicit in type hint but check for None if passed dynamically)
    if not manifest.harness:
        rejection_reasons.append("Missing harness identity.")

    # 2. Check for explicit stop conditions (scaffolded)
    stop_conditions = ["session_timeout", "manual_interrupt", "security_violation"]

    if rejection_reasons:
        return PlayerAdmissionRecord(
            player_id=player_id,
            session_manifest=None,
            admission_status="rejected",
            rejection_reasons=rejection_reasons,
            stop_conditions=stop_conditions
        )

    return PlayerAdmissionRecord(
        player_id=player_id,
        session_manifest=manifest,
        admission_status="admitted",
        rejection_reasons=[],
        stop_conditions=stop_conditions
    )

def to_dict(obj: Any) -> Dict[str, Any]:
    """JSON-safe serialization helper."""
    if dataclasses.is_dataclass(obj):
        return {k: to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    elif isinstance(obj, list):
        return [to_dict(v) for v in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj
