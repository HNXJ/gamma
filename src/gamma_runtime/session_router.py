from __future__ import annotations
from dataclasses import dataclass, field
import os
import re

@dataclass(frozen=True)
class ModelLane:
    lane_id: str
    role: str
    host: str
    canonical_model_id: str
    runtime_instance_id: str | None = None
    vision_mode: str = "unverified_configured_by_doctrine"
    runtime_instance_suffix_policy: str = "observe_only_never_request"
    max_parallel_observed: int | None = None
    truth_mode: str = "truth_safe_unverified"

@dataclass(frozen=True)
class PlayerProfile:
    player_profile_id: str
    role: str
    lane_id: str
    canonical_model_id: str
    allowed_claim_types: list[str] = field(default_factory=lambda: ["proposal_value", "simulation_result", "rejected_invalid", "runtime_validation"])
    artifact_policy: str = "persist_all"
    transcript_policy: str = "persist_all"
    truth_mode: str = "truth_safe_unverified"
    truth_bearing_run: bool = False

@dataclass(frozen=True)
class SessionBinding:
    session_id: str
    harness_id: str
    player_profile_id: str
    lane_id: str
    canonical_model_id: str
    runtime_instance_id: str | None
    transcript_path: str
    artifact_root: str
    claim_type_default: str
    truth_mode: str
    truth_bearing_run: bool

class SessionRouter:
    def __init__(self, run_root: str):
        self.run_root = run_root
        self.lanes: dict[str, ModelLane] = {}
        self.profiles: dict[str, PlayerProfile] = {}
        self.bindings: dict[str, SessionBinding] = {}
        self.quarantined_models = {"gemma-4-e4b-it-mxfp8"}

    def register_lane(self, lane: ModelLane):
        self._validate_model_id(lane.canonical_model_id)
        self.lanes[lane.lane_id] = lane

    def register_profile(self, profile: PlayerProfile):
        if profile.lane_id not in self.lanes:
            raise ValueError(f"Lane {profile.lane_id} not registered")
        lane = self.lanes[profile.lane_id]
        if profile.canonical_model_id != lane.canonical_model_id:
             raise ValueError(f"Profile model {profile.canonical_model_id} mismatch with lane {lane.canonical_model_id}")
        self.profiles[profile.player_profile_id] = profile

    def bind_session(self, session_id: str, player_profile_id: str, harness_id: str) -> SessionBinding:
        if player_profile_id not in self.profiles:
            raise ValueError(f"Profile {player_profile_id} not registered")
        profile = self.profiles[player_profile_id]
        lane = self.lanes[profile.lane_id]

        transcript_path = os.path.normpath(os.path.join(self.run_root, "transcripts", f"{session_id}.jsonl"))
        artifact_root = os.path.normpath(os.path.join(self.run_root, "artifacts", session_id))

        binding = SessionBinding(
            session_id=session_id,
            harness_id=harness_id,
            player_profile_id=player_profile_id,
            lane_id=profile.lane_id,
            canonical_model_id=profile.canonical_model_id,
            runtime_instance_id=lane.runtime_instance_id,
            transcript_path=transcript_path,
            artifact_root=artifact_root,
            claim_type_default=profile.allowed_claim_types[0] if profile.allowed_claim_types else "proposal_value",
            truth_mode=profile.truth_mode,
            truth_bearing_run=profile.truth_bearing_run
        )
        self.bindings[session_id] = binding
        return binding

    def _validate_model_id(self, model_id: str):
        if model_id in self.quarantined_models:
            raise ValueError(f"Model {model_id} is quarantined")
        if re.search(r":\d+$", model_id):
            raise ValueError(f"Canonical model ID {model_id} cannot contain runtime suffix")

    def get_lms_request_model(self, session_id: str) -> str:
        if session_id not in self.bindings:
             raise ValueError(f"Session {session_id} not bound")
        binding = self.bindings[session_id]
        return binding.canonical_model_id

    @staticmethod
    def create_office_mac_standard_topology(run_root: str) -> SessionRouter:
        router = SessionRouter(run_root)
        
        # 1. Register Lanes
        router.register_lane(ModelLane(
            lane_id="office_mac_gemma_player_lane",
            role="scientific_worker",
            host="100.69.184.42",
            canonical_model_id="gemma-4-e4b-it-mlx"
        ))
        router.register_lane(ModelLane(
            lane_id="office_mac_gptoss_judge_lane",
            role="judge_critic",
            host="100.69.184.42",
            canonical_model_id="gpt-oss-20b"
        ))
        
        # 2. Register Profiles (8 per lane)
        for i in range(1, 9):
            router.register_profile(PlayerProfile(
                player_profile_id=f"office_mac_gemma_player_{i:02}",
                role="scientific_worker",
                lane_id="office_mac_gemma_player_lane",
                canonical_model_id="gemma-4-e4b-it-mlx"
            ))
            router.register_profile(PlayerProfile(
                player_profile_id=f"office_mac_gptoss_judge_{i:02}",
                role="judge_critic",
                lane_id="office_mac_gptoss_judge_lane",
                canonical_model_id="gpt-oss-20b"
            ))
            
        return router
