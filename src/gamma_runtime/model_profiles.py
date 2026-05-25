import dataclasses
from typing import Dict, Optional, List
import re

@dataclasses.dataclass
class ModelProfile:
    profile_id: str
    host: str
    canonical_model_id: str
    route_ready: bool
    blocked_reason: Optional[str] = None
    
    def __post_init__(self):
        # 21. suffix ids must not be canonical
        if re.search(r":\d+$", self.canonical_model_id):
            raise ValueError(f"Model ID '{self.canonical_model_id}' contains forbidden runtime suffix.")

class ProfileRegistry:
    def __init__(self):
        self.profiles: Dict[str, ModelProfile] = {}
        
    def register(self, profile: ModelProfile):
        self.profiles[profile.profile_id] = profile
        
    def register_default_profiles(self):
        # Phase 2 route-safe profiles
        self.register(ModelProfile(
            profile_id="gemma4-parallel",
            host="office-mac",
            canonical_model_id="gemma-4-e4b-it",
            route_ready=True
        ))
        self.register(ModelProfile(
            profile_id="gemma-9b-schiz",
            host="office-mac",
            canonical_model_id="gemma-2-9b-it",
            route_ready=True
        ))
        
        # 26B/31B load-blocked profiles
        self.register(ModelProfile(
            profile_id="gemma-26b-blocked",
            host="office-mac",
            canonical_model_id="gemma-2-27b-it",
            route_ready=False,
            blocked_reason="Load-blocked 26B/31B profile not route-safe."
        ))
        self.register(ModelProfile(
            profile_id="gemma-31b-blocked",
            host="office-mac",
            canonical_model_id="gemma-2-31b-it",
            route_ready=False,
            blocked_reason="Load-blocked 26B/31B profile not route-safe."
        ))
