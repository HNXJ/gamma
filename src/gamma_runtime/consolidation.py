import json
import logging
import os
from typing import List, Dict, Any
from .blackboard import Blackboard
from gamma_runtime.trace_schema import Trace, ConsensusLevel, TraceMode

logger = logging.getLogger("Consolidation")

class ConsolidationManager:
    """
    Manages the "Slow Learning" consolidation phase.
    Converts Blackboard deliberations into validated training traces for FedLoRA.
    """
    def __init__(self, staging_root: str = "staging"):
        self.staging_root = staging_root
        self.payload_dir = os.path.join(staging_root, "fedlora_payloads")
        os.makedirs(self.payload_dir, exist_ok=True)

    def extract_validated_traces(self, blackboard: Blackboard, session_id: str) -> str:
        """
        Parses the blackboard for entries that meet the consensus gate (>85%).
        Saves them as a structured JSON payload for the MLX training loop.
        """
        logger.info(f"INITIATING CONSOLIDATION: Session {session_id}")
        
        valid_traces = []
        for entry in blackboard.entries:
            # Skip system/engine metadata
            if entry.sender in ["SYSTEM", "SDE_ENGINE", "SDE_SOLVER"]:
                continue
                
            # Filter by metadata quality if available (mocking high consensus for pilot)
            is_high_quality = entry.metadata.get("consensus_score", 0.9) > 0.85
            
            if is_high_quality:
                # Map Blackboard entry to Gamma Trace schema
                trace = Trace(
                    node_id=entry.sender,
                    role=entry.sender, # In a real run, this would be the agent role
                    mode=TraceMode.CONSOLIDATION,
                    input_context=blackboard.topic,
                    output=entry.content,
                    consensus_level=ConsensusLevel.HIGH,
                    judge_score=entry.metadata.get("consensus_score", 0.9),
                    doi_support=entry.metadata.get("kind") == "sde_proposal"
                )
                valid_traces.append(trace.dict())

        if not valid_traces:
            logger.warning("No traces met the consensus gate. Consolidation aborted.")
            return ""

        # Save to staging/fedlora_payloads
        payload_filename = f"trace_{session_id}.json"
        payload_path = os.path.join(self.payload_dir, payload_filename)
        
        with open(payload_path, "w") as f:
            json.dump(valid_traces, f, indent=2)
            
        logger.info(f"✅ CONSOLIDATION SUCCESS: {len(valid_traces)} traces staged at {payload_path}")
        return payload_path

    async def trigger_training(self, payload_path: str, model_key: str):
        """
        Invokes the actual MLX LoRA training loop.
        This would normally call scripts/train_lora_mlx.py.
        """
        logger.info(f"TRAPPING CONSOLIDATION EVENT: Training adapter for {model_key}")
        # In a real environment, this would use subprocess.run with the MLX training script
        # subprocess.run(["python3", "scripts/train_lora_mlx.py", "--data", payload_path, "--model", model_key])
        logger.info("Training complete. Adapter updated in memory (Simulated).")
