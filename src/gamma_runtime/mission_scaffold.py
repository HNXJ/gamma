"""
Mission scaffold for Gamma Labyrinth.
Defines metadata for upcoming player missions.
"""

from typing import List, Literal

EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01 = "EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01"

MISSION_METADATA = {
    EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01: {
        "mission_id": EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01,
        "description": "jaxfne latent dynamics proxy mission - proxy readout only",
        "allowed_planes": ["Execution", "Observation"],
        "excluded_tools": ["Kilosort4"],
        "required_admission": True,
        "claim_type": "proposal_value", # or simulation_result
        "truth_status": "truth_safe_unverified",
        "claim_level": "proxy_readout_only",
        "prohibited_actions": ["raw_data_processing", "spike_sorting", "truth_mutation"]
    }
}

def get_mission_config(mission_id: str):
    return MISSION_METADATA.get(mission_id)
