import dataclasses
from typing import Dict, Optional, List
import re

@dataclasses.dataclass
class ModelProfile:
    profile_id: str
    host: str
    canonical_model_id: str
    status: str # mock_safe, dry_run_safe, live_candidate_unverified, load_blocked, blocked, unknown_unverified
    blocked_reason: Optional[str] = None

    def __post_init__(self):
        # 21. suffix ids must not be canonical
        if re.search(r":\d+$", self.canonical_model_id):
            raise ValueError(f"Model ID '{self.canonical_model_id}' contains forbidden runtime suffix.")

    @property
    def route_ready(self) -> bool:
        """Doctrine: route_ready is only true if status is mock_safe or dry_run_safe for now."""
        return self.status in ["mock_safe", "dry_run_safe"]

class ProfileRegistry:
    def __init__(self):
        self.profiles: Dict[str, ModelProfile] = {}

    def register(self, profile: ModelProfile):
        self.profiles[profile.profile_id] = profile

    def register_default_profiles(self):
        # Phase 2 mock-safe profiles
        self.register(ModelProfile(
            profile_id="gemma4-parallel",
            host="office-mac",
            canonical_model_id="gemma-4-e4b-it",
            status="mock_safe"
        ))
        self.register(ModelProfile(
            profile_id="gemma-9b-schiz",
            host="office-mac",
            canonical_model_id="gemma-2-9b-it",
            status="mock_safe"
        ))

        # Doctrine load-blocked Gemma 4 profiles
        self.register(ModelProfile(
            profile_id="gemma-4-26b-a4b-it",
            host="office-mac",
            canonical_model_id="gemma-4-26b-a4b-it",
            status="load_blocked",
            blocked_reason="Doctrine: load-blocked 26B/31B profile not route-safe."
        ))
        self.register(ModelProfile(
            profile_id="gemma-4-31b-it",
            host="office-mac",
            canonical_model_id="gemma-4-31b-it",
            status="load_blocked",
            blocked_reason="Doctrine: load-blocked 26B/31B profile not route-safe."
        ))

        # Other blocked profiles from previous commit (mapping to doctrine if applicable, or keeping as blocked)
        self.register(ModelProfile(
            profile_id="gemma-26b-blocked",
            host="office-mac",
            canonical_model_id="gemma-2-27b-it",
            status="blocked",
            blocked_reason="Explicitly blocked per local runtime policy."
        ))
        self.register(ModelProfile(
            profile_id="gemma-31b-blocked",
            host="office-mac",
            canonical_model_id="gemma-2-31b-it",
            status="blocked",
            blocked_reason="Explicitly blocked per local runtime policy."
        ))

    def get_mock_safe_profiles(self) -> List[ModelProfile]:
        return [p for p in self.profiles.values() if p.status == "mock_safe"]

    def get_live_candidates_unverified(self) -> List[ModelProfile]:
        return [p for p in self.profiles.values() if p.status == "live_candidate_unverified"]

    def get_blocked_profiles(self) -> List[ModelProfile]:
        return [p for p in self.profiles.values() if p.status in ["blocked", "load_blocked"]]

    def is_selectable_for_mode(self, profile_id: str, mode: str) -> bool:
        profile = self.profiles.get(profile_id)
        if not profile:
            return False
        if mode == "mock":
            return profile.status in ["mock_safe", "dry_run_safe", "live_candidate_unverified"]
        if mode == "live":
            # Live is never selectable without explicit verified status (not implemented yet)
            return False
        return False
