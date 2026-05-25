import pytest
import re
from gamma_runtime.model_profiles import ProfileRegistry, ModelProfile

def test_doctrine_blocked_profiles():
    reg = ProfileRegistry()
    reg.register_default_profiles()
    
    blocked = reg.get_blocked_profiles()
    blocked_ids = [p.canonical_model_id for p in blocked]
    
    # Doctrine: gemma-4-26b-a4b-it and gemma-4-31b-it must be blocked
    assert "gemma-4-26b-a4b-it" in blocked_ids
    assert "gemma-4-31b-it" in blocked_ids
    
    for p in blocked:
        assert p.status in ["load_blocked", "blocked"]
        assert p.route_ready is False

def test_selectable_for_mode():
    reg = ProfileRegistry()
    reg.register_default_profiles()
    
    # Blocked should not be selectable for mock or live
    assert reg.is_selectable_for_mode("gemma-4-26b-a4b-it", "mock") is False
    assert reg.is_selectable_for_mode("gemma-4-26b-a4b-it", "live") is False
    
    # Mock safe should be selectable for mock but not live
    assert reg.is_selectable_for_mode("gemma4-parallel", "mock") is True
    assert reg.is_selectable_for_mode("gemma4-parallel", "live") is False

def test_no_suffix_in_canonical_id():
    # Should raise ValueError if suffix exists
    with pytest.raises(ValueError, match="contains forbidden runtime suffix"):
        ModelProfile(
            profile_id="bad-profile",
            host="localhost",
            canonical_model_id="gemma-2-9b-it:2",
            status="mock_safe"
        )

def test_route_ready_labels():
    reg = ProfileRegistry()
    reg.register_default_profiles()
    
    # Check that none are 'route_ready' in the status field, they use mock_safe etc.
    for p in reg.profiles.values():
        assert p.status != "route_ready"
        if p.status == "mock_safe":
            assert p.route_ready is True
        else:
            assert p.route_ready is False
