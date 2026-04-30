import json
import logging
import os
from typing import Dict, Any, List, Optional
from src.gamma_runtime.types import MissionContext

logger = logging.getLogger("ExecutionAdapter")

class ExecutionAdapter:
    """
    Stage 2 Execution Adapter / Proposal Materializer.
    Converts a mission-aligned proposal JSON into an executable solver config.
    Acts as the second trust boundary for the Execution Plane.
    """
    def __init__(self, proposals_dir: str):
        self.proposals_dir = proposals_dir

    def materialize_proposal(self, proposal_id: str, mission_context: MissionContext) -> Dict[str, Any]:
        """
        Re-validates and materializes a proposal into a solver-ready executable state.
        Ensures provenance and mission alignment at execution ingress.
        """
        filename = os.path.join(self.proposals_dir, f"{proposal_id}.json")
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Execution Failure: Proposal artifact not found: {filename}")

        with open(filename, 'r') as f:
            proposal = json.load(f)

        # 1. Execution-Ingress Re-validation
        meta = proposal.get("meta", {})
        proposal_n = meta.get("neuron_count")

        if proposal_n is None:
            raise ValueError(f"Execution Rejected: Proposal {proposal_id} lacks 'meta.neuron_count'.")
        
        if proposal_n != mission_context.target_neuron_count:
            raise ValueError(
                f"Execution Rejected: Mission Mismatch. "
                f"Proposal N={proposal_n} != Target N={mission_context.target_neuron_count}"
            )

        # 2. Materialization Logic: Minimal Executable Representation
        # For Stage 2B, we add explicit provenance tagging.
        run_id = f"run_{int(os.times()[4])}_{proposal_id[-8:]}"
        executable_config = {
            "proposal_id": proposal_id,
            "neuron_count": proposal_n,
            "params": proposal.get("params", {}),
            "mission_topic": mission_context.mission_topic,
            "provenance": {
                "materialized_by": "ExecutionAdapter",
                "run_id": run_id,
                "timestamp": os.times()[4]
            }
        }

        logger.info(f"🚀 Proposal {proposal_id} materialized for N={proposal_n} (Run ID: {run_id}).")
        return executable_config

    def verify_substrate_success(self, metadata: Dict[str, Any], target_count: int) -> bool:
        """
        Verifies if a simulation run satisfies the pass-criteria for the target count.
        Stage 2B: Enforces strict provenance validation.
        """
        converged = metadata.get("converged", False)
        count_match = metadata.get("neuron_count") == target_count
        
        # Provenance Sealing: Only adapter-mediated runs are persistence-eligible
        provenance = metadata.get("provenance", {})
        is_canonical = provenance.get("materialized_by") == "ExecutionAdapter"
        
        if not is_canonical:
            logger.warning("🚫 PERSISTENCE REJECTED: Result lacks canonical 'ExecutionAdapter' provenance.")

        return converged and count_match and is_canonical
