import pytest
from gamma_runtime.model_profiles import ModelProfile, ProfileRegistry, create_office_mac_gemma4_profiles

def test_model_profile_validation():
    # Valid profile
    p = ModelProfile(
        profile_id="test_profile",
        host="test_host",
        base_url="http://localhost:1234",
        gamma_display_name="test-model",
        lms_canonical_model_id="test-model-id"
    )
    p.validate()

    # Reject runtime suffix
    with pytest.raises(ValueError, match="cannot contain runtime suffix"):
        p_suffix = ModelProfile(
            profile_id="test_profile",
            host="test_host",
            base_url="http://localhost:1234",
            gamma_display_name="test-model",
            lms_canonical_model_id="test-model-id:1"
        )
        p_suffix.validate()

    # Quarantine logic tests
    quarantine_cases = [
        ("gemma-4-e4b-it-mxfp8", "gemma-4-e4b-it-mxfp8"),
        ("gemma-4-31b-it-mxfp8", "gemma-4-31b-it"),
        ("gemma-4-31b-it-mxfp8-mlx", "gemma-4-31b-it"),
        ("gemma-4-26b-a4b-it-claude-opus-distilled-v2-mlx-mxfp8", "gemma-4-26b-a4b-it"),
        ("gemma-4-26b-a4b-heretic-mlx", "gemma-4-26b-a4b-it"),
    ]

    for display_name, canonical_id in quarantine_cases:
        with pytest.raises(ValueError, match="matches quarantine pattern"):
            p_quarantine = ModelProfile(
                profile_id="test_profile",
                host="test_host",
                base_url="http://localhost:1234",
                gamma_display_name=display_name,
                lms_canonical_model_id=canonical_id
            )
            p_quarantine.validate()

    # Reject vision for Gemma 4
    with pytest.raises(ValueError, match="Vision/VLM must be disabled"):
        p_vision = ModelProfile(
            profile_id="test_profile",
            host="test_host",
            base_url="http://localhost:1234",
            gamma_display_name="gemma-4-31b-it-mxfp4",
            lms_canonical_model_id="gemma-4-31b-it",
            vision_mode="enabled",
            vlm_enabled=True
        )
        p_vision.validate()

def test_office_mac_gemma4_profiles_load_blocked():
    # Even if they are in inventory, they should be marked load_blocked now
    inventory = ["gemma-4-31b-it", "gemma-4-26b-a4b-it"]
    profiles = create_office_mac_gemma4_profiles(inventory)
    
    assert len(profiles) == 2
    
    for p in profiles:
        assert p.profile_status == "load_blocked"
        assert p.block_reason == "MODEL_LOAD_BLOCKED_BASELINE"
        assert p.last_load_diagnosis is not None
        assert p.evidence_path is not None
        assert p.is_route_ready() is False
        # Verify desired settings are preserved
        assert p.context_length_tokens == 65536
        assert p.max_concurrent_predictions == 8
        assert p.vision_mode == "disabled"
        assert p.vlm_enabled is False

def test_route_readiness_logic():
    p_ready = ModelProfile(
        profile_id="ready_p", host="h", base_url="u", gamma_display_name="d",
        lms_canonical_model_id="m", profile_status="ready"
    )
    p_blocked = ModelProfile(
        profile_id="blocked_p", host="h", base_url="u", gamma_display_name="d",
        lms_canonical_model_id="m", profile_status="load_blocked"
    )
    p_pending = ModelProfile(
        profile_id="pending_p", host="h", base_url="u", gamma_display_name="d",
        lms_canonical_model_id="m", profile_status="download_pending"
    )

    assert p_ready.is_route_ready() is True
    assert p_blocked.is_route_ready() is False
    assert p_pending.is_route_ready() is False

    registry = ProfileRegistry()
    registry.register(p_ready)
    registry.register(p_blocked)
    registry.register(p_pending)

    ready_list = registry.route_ready_profiles()
    assert len(ready_list) == 1
    assert ready_list[0].profile_id == "ready_p"

def test_download_pending_status():
    profiles = create_office_mac_gemma4_profiles([])
    for p in profiles:
        assert p.profile_status == "download_pending"
        assert p.is_route_ready() is False

def test_distinct_profile_ids():
    profiles = create_office_mac_gemma4_profiles([])
    profile_ids = [p.profile_id for p in profiles]
    assert len(profile_ids) == len(set(profile_ids))
    assert "31b" in profile_ids[0]
    assert "26b" in profile_ids[1]
