import pytest
from gamma_runtime.mission_scaffold import get_mission_config, EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01

def test_mission_scaffold_boundaries():
    """Assert Labyrinth mission boundaries and drift correction."""

    config = get_mission_config(EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01)

    assert config is not None

    # 1. Kilosort4 Excluded (Drift Correction)
    assert "Kilosort4" in config["excluded_tools"]

    # 2. Correct Planes (Plane Separation)
    assert "Execution" in config["allowed_planes"]
    assert "Observation" in config["allowed_planes"]
    assert "Truth" not in config["allowed_planes"]

    # 3. Truth Status (Truth Safety)
    assert config["truth_status"] == "truth_safe_unverified"

    # 4. Claim Level (Proxy only)
    assert config["claim_level"] == "proxy_readout_only"

    # 5. Required Admission
    assert config["required_admission"] is True

    # 6. Prohibited Actions (No raw data/spike sorting)
    assert "raw_data_processing" in config["prohibited_actions"]
    assert "spike_sorting" in config["prohibited_actions"]
    assert "truth_mutation" in config["prohibited_actions"]

def test_no_kilosort4_in_any_mission():
    """Ensure Kilosort4 is not accidentally admitted into any Labyrinth mission scaffold."""
    from gamma_runtime.mission_scaffold import MISSION_METADATA

    for mission_id, config in MISSION_METADATA.items():
        assert "Kilosort4" in config.get("excluded_tools", [])
        assert "spike_sorting" in config.get("prohibited_actions", [])
        assert "Truth" not in config.get("allowed_planes", [])

def test_jaxfne_representation():
    """jaxfne must be represented only as a proxy mission/tool candidate."""
    config = get_mission_config(EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01)
    assert "jaxfne" in config["description"]
    assert config["claim_level"] == "proxy_readout_only"
