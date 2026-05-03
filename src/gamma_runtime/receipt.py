import os
import json
import uuid
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ReceiptManager")

class ReceiptManager:
    """
    Manages execution receipts for Gamma.
    Receipts provide a non-mutable audit trail of agent proposals and simulation results.
    """
    def __init__(self, receipts_dir: Optional[str] = None):
        # Use workspace-relative path if not provided
        if receipts_dir is None:
            self.receipts_dir = "local/run/receipts"
        else:
            self.receipts_dir = receipts_dir
            
        try:
            os.makedirs(self.receipts_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create receipts directory {self.receipts_dir}: {str(e)}")

    def emit_receipt(
        self,
        run_id: str,
        agent_id: str,
        proposal_id: Optional[str] = None,
        parameters_extracted: Optional[Dict[str, Any]] = None,
        proposal_parse_status: str = "success",
        simulation_executed: bool = True,
        gate_result: str = "PASS",
        gate_reason: str = "Success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Emits a structured execution receipt to a local file.
        """
        receipt_id = f"rcpt-{uuid.uuid4().hex[:8]}"
        receipt = {
            "schema_version": "1.0.0",
            "receipt_id": receipt_id,
            "run_id": run_id,
            "timestamp": time.time(),
            "agent_id": agent_id,
            "proposal_id": proposal_id,
            "parameters_extracted": parameters_extracted or {},
            "proposal_parse_status": proposal_parse_status,
            "simulation_executed": simulation_executed,
            "gate_result": gate_result,
            "gate_reason": gate_reason,
            "promoted_to_truth": False,
            "metadata": metadata or {}
        }
        
        path = os.path.join(self.receipts_dir, f"{receipt_id}.json")
        try:
            with open(path, "w") as f:
                json.dump(receipt, f, indent=2)
            logger.info(f"Emitted receipt {receipt_id} to {path}")
        except Exception as e:
            logger.error(f"Failed to write receipt {receipt_id}: {str(e)}")
            
        return path
