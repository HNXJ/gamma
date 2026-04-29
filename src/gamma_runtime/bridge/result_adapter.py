import json
from dataclasses import asdict
from .bridge_contract import ScientificResult

class ResultAdapter:
    @staticmethod
    def to_blackboard_str(result: ScientificResult) -> str:
        """
        Compresses scientific truth into a runtime-safe string summary for the blackboard.
        """
        data = asdict(result)
        summary = {
            "proposal_id": data["proposal_id"],
            "status": data["status"],
            "stability": data.get("healthy", {}).get("stability_pass", False),
            "rejection_reason": data["rejection_reason"],
            "artifacts": data["artifacts"]
        }
        
        if data["status"] == "accepted":
            summary["gamma_ratios"] = {
                "healthy": data["healthy"],
                "schiz": data["schiz"]
            }
            
        return "BLACKBOARD UPDATE from bridge:\n" + json.dumps(summary, indent=2)
