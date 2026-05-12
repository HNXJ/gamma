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

def test_office_mac_gemma4_profiles():
    inventory = ["gemma-4-31b-it", "gemma-4-26b-a4b-it"]
    profiles = create_office_mac_gemma4_profiles(inventory)
    
    assert len(profiles) == 2
    
    p31b = next(p for p in profiles if "31b" in p.profile_id)
    assert p31b.context_length_tokens == 65536
    assert p31b.max_concurrent_predictions == 8
    assert p31b.vision_mode == "disabled"
    assert p31b.vlm_enabled is False
    assert p31b.profile_status == "ready"

    p26b = next(p for p in profiles if "26b" in p.profile_id)
    assert p26b.context_length_tokens == 65536
    assert p26b.max_concurrent_predictions == 8
    assert p26b.vision_mode == "disabled"
    assert p26b.vlm_enabled is False
    assert p26b.profile_status == "ready"

def test_download_pending_status():
    profiles = create_office_mac_gemma4_profiles([])
    for p in profiles:
        assert p.profile_status == "download_pending"

def test_distinct_profile_ids():
    profiles = create_office_mac_gemma4_profiles([])
    profile_ids = [p.profile_id for p in profiles]
    assert len(profile_ids) == len(set(profile_ids))
    assert "31b" in profile_ids[0]
    assert "26b" in profile_ids[1]
