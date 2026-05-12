from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Any
import re

@dataclass(frozen=True)
class ModelProfile:
    profile_id: str
    host: str
    base_url: str
    gamma_display_name: str
    lms_canonical_model_id: str
    runtime_instance_id: str | None = None
    quantization: str = "unknown"
    context_length_tokens: int = 4096
    max_concurrent_predictions: int = 1
    vision_mode: str = "disabled"
    vlm_enabled: bool = False
    runtime_suffix_policy: str = "observe_only_never_request"
    truth_mode: str = "truth_safe_unverified"
    truth_bearing_run: bool = False
    profile_status: Literal["ready", "download_pending", "blocked"] = "blocked"

    def validate(self):
        # 1. Reject runtime suffix in canonical ID
        if re.search(r":\d+$", self.lms_canonical_model_id):
            raise ValueError(f"Canonical model ID {self.lms_canonical_model_id} cannot contain runtime suffix")

        # 2. Centralized Quarantine/Deny Patterns
        deny_patterns = [
            r"mxfp8",
            r"heretic",
            r"claude-opus-distilled",
            r"gemma-4-e4b-it-mxfp8"
        ]
        for pattern in deny_patterns:
            if re.search(pattern, self.lms_canonical_model_id, re.IGNORECASE):
                raise ValueError(f"Model ID '{self.lms_canonical_model_id}' matches quarantine pattern '{pattern}'")
            if re.search(pattern, self.gamma_display_name, re.IGNORECASE):
                raise ValueError(f"Display name '{self.gamma_display_name}' matches quarantine pattern '{pattern}'")

        # 3. Mission-specific Gemma 4 constraints
        if self.vision_mode != "disabled" or self.vlm_enabled:
             # Mission constraint: vision must be disabled for these profiles
             if "gemma-4" in self.lms_canonical_model_id:
                 raise ValueError("Vision/VLM must be disabled for Gemma 4 profiles in this configuration")

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "host": self.host,
            "base_url": self.base_url,
            "gamma_display_name": self.gamma_display_name,
            "lms_canonical_model_id": self.lms_canonical_model_id,
            "runtime_instance_id": self.runtime_instance_id,
            "quantization": self.quantization,
            "context_length_tokens": self.context_length_tokens,
            "max_concurrent_predictions": self.max_concurrent_predictions,
            "vision_mode": self.vision_mode,
            "vlm_enabled": self.vlm_enabled,
            "runtime_suffix_policy": self.runtime_suffix_policy,
            "truth_mode": self.truth_mode,
            "truth_bearing_run": self.truth_bearing_run,
            "profile_status": self.profile_status
        }

class ProfileRegistry:
    def __init__(self):
        self.profiles: dict[str, ModelProfile] = {}

    def register(self, profile: ModelProfile):
        profile.validate()
        self.profiles[profile.profile_id] = profile

    def get_profile(self, profile_id: str) -> ModelProfile:
        if profile_id not in self.profiles:
            raise KeyError(f"Profile {profile_id} not found")
        return self.profiles[profile_id]

def create_office_mac_gemma4_profiles(inventory_keys: list[str]) -> list[ModelProfile]:
    profiles = []
    
    # 31B Profile
    id_31b = "gemma-4-31b-it"
    status_31b = "ready" if id_31b in inventory_keys else "download_pending"
    profiles.append(ModelProfile(
        profile_id="office_mac_gemma4_31b_it_mxfp4",
        host="office_mac_kelvin_lms",
        base_url="http://100.69.184.42:1234",
        gamma_display_name="gemma-4-31b-it-mxfp4",
        lms_canonical_model_id=id_31b,
        quantization="MXFP4",
        context_length_tokens=65536,
        max_concurrent_predictions=8,
        profile_status=status_31b
    ))

    # 26B Profile
    id_26b = "gemma-4-26b-a4b-it"
    status_26b = "ready" if id_26b in inventory_keys else "download_pending"
    profiles.append(ModelProfile(
        profile_id="office_mac_gemma4_26b_a4b_it_mxfp4",
        host="office_mac_kelvin_lms",
        base_url="http://100.69.184.42:1234",
        gamma_display_name="gemma-4-26b-a4b-it-mxfp4",
        lms_canonical_model_id=id_26b,
        quantization="MXFP4",
        context_length_tokens=65536,
        max_concurrent_predictions=8,
        profile_status=status_26b
    ))

    return profiles
