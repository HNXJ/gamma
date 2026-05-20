"""
jaxfne proxy mission recipe for Gamma Labyrinth.
Handles the definition and mock execution of jaxfne-style proxy missions.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from .mission_scaffold import get_mission_config, EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01
from .harness_registry import PlayerAdmissionRecord

class JaxfneProxyMissionRecipe:
    """
    Defines a bounded mission recipe for jaxfne proxy simulations.
    """
    def __init__(self, mission_id: str = EVT_JAXFNE_LATENT_DYNAMICS_PROXY_MISSION_01):
        self.mission_id = mission_id
        self.config = get_mission_config(mission_id)
        if not self.config:
            raise ValueError(f"Unknown mission ID: {mission_id}")

    def create_execution_plan(self, admission_record: PlayerAdmissionRecord, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an execution plan based on the admission record and parameters.
        """
        if admission_record.admission_status != "admitted":
            raise ValueError("Player must be admitted before creating an execution plan.")

        # Ensure Kilosort4 is not in the execution params
        if "Kilosort4" in str(params):
            raise ValueError("Kilosort4 is prohibited in Labyrinth core missions.")

        # Ensure the config explicitly excludes it (double check the scaffold boundary)
        if "Kilosort4" not in self.config.get("excluded_tools", []):
            raise ValueError("Mission configuration must explicitly exclude Kilosort4.")

        plan = {
            "mission_id": self.mission_id,
            "session_id": admission_record.session_manifest.session_id,
            "player_id": admission_record.player_id,
            "params": params,
            "constraints": self.config,
            "timestamp": datetime.now().isoformat()
        }
        return plan

    def run_proxy_mission(self, admission_record: PlayerAdmissionRecord, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs a mock proxy mission and returns a receipt candidate.
        No actual jaxfne execution happens here - it's a metadata-only mock.
        """
        plan = self.create_execution_plan(admission_record, params)
        
        # Mock result generation
        receipt_candidate = {
            "receipt_type": "jaxfne_proxy_mission_receipt",
            "mission_id": self.mission_id,
            "session_id": plan["session_id"],
            "player_id": plan["player_id"],
            "status": "success",
            "claim_type": self.config["claim_type"],
            "claim_level": self.config["claim_level"],
            "truth_status": self.config["truth_status"],
            "output_summary": {
                "message": "jaxfne proxy simulation completed (mock)",
                "latent_dimensions": params.get("latent_dims", 4),
                "simulation_steps": params.get("steps", 100),
                "result_checksum": "sha256:mock_jaxfne_result_checksum"
            },
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "excluded_tools": self.config["excluded_tools"],
                "prohibited_actions": self.config["prohibited_actions"]
            }
        }
        
        return receipt_candidate

def run_jaxfne_mission_recipe(admission_record: PlayerAdmissionRecord, params: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to run the jaxfne recipe."""
    recipe = JaxfneProxyMissionRecipe()
    return recipe.run_proxy_mission(admission_record, params)
