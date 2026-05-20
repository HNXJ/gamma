import pytest
import json
from gamma_runtime.lms_interface import LMSProviderSpec, LMSModelSpec
from gamma_runtime.lms_harness_bridge import admit_lms_player
from gamma_runtime.jaxfne_proxy_mission_recipe import run_jaxfne_mission_recipe, JaxfneProxyMissionRecipe
from gamma_runtime.mission_scaffold import EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01

@pytest.fixture
def mock_admission():
    provider = LMSProviderSpec(
        provider_id="test_provider",
        role="test_role",
        base_url="http://localhost:1234",
        route_ready=True
    )
    model = LMSModelSpec(
        model_id="test_model",
        model_family="test_family",
        model_label="Test Model",
        route_ready=True
    )
    return admit_lms_player(
        session_id="test_session",
        player_id="test_player",
        model_spec=model,
        provider_spec=provider,
        mock_live_mode="mock"
    )

def test_jaxfne_proxy_mission_recipe_execution(mock_admission):
    """Confirm the jaxfne proxy mission recipe runs and respects boundaries."""
    
    params = {
        "latent_dims": 8,
        "steps": 200,
        "seed": 42
    }
    
    receipt = run_jaxfne_mission_recipe(mock_admission, params)
    
    assert receipt["receipt_type"] == "jaxfne_proxy_mission_receipt"
    assert receipt["mission_id"] == EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01
    assert receipt["status"] == "success"
    
    # 1. Plane & Truth Separation
    assert receipt["truth_status"] == "truth_safe_unverified"
    assert receipt["claim_type"] == "proposal_value"
    assert receipt["claim_level"] == "proxy_readout_only"
    
    # 2. Drift Correction (Kilosort4 Excluded)
    assert "Kilosort4" in receipt["metadata"]["excluded_tools"]
    
    # 3. Output Summary
    assert receipt["output_summary"]["latent_dimensions"] == 8
    assert receipt["output_summary"]["simulation_steps"] == 200
    
    # 4. JSON-safe
    json_str = json.dumps(receipt)
    assert isinstance(json_str, str)

def test_recipe_rejects_unadmitted_player():
    """Recipe should fail if player is not admitted."""
    from gamma_runtime.harness_registry import PlayerAdmissionRecord
    
    bad_record = PlayerAdmissionRecord(
        player_id="bad_player",
        session_manifest=None,
        admission_status="rejected",
        rejection_reasons=["test_rejection"],
        stop_conditions=["test_stop"]
    )
    
    recipe = JaxfneProxyMissionRecipe()
    with pytest.raises(ValueError, match="Player must be admitted"):
        recipe.run_proxy_mission(bad_record, {})

def test_recipe_prohibits_kilosort4(mock_admission):
    """Recipe must explicitly reject Kilosort4 if mentioned in params."""
    
    params = {
        "tool": "Kilosort4",
        "action": "spike_sorting"
    }
    
    recipe = JaxfneProxyMissionRecipe()
    with pytest.raises(ValueError, match="Kilosort4 is prohibited"):
        recipe.run_proxy_mission(mock_admission, params)

def test_no_truth_mutation_in_receipt(mock_admission):
    """Ensure no truth mutation signals are present in the output."""
    receipt = run_jaxfne_mission_recipe(mock_admission, {})
    
    assert "truth_mutation" in receipt["metadata"]["prohibited_actions"]
    assert "spike_sorting" in receipt["metadata"]["prohibited_actions"]
    # Double check truth_status is never promoted here
    assert receipt["truth_status"] == "truth_safe_unverified"
