import json
import re
from typing import Optional
from .bridge_contract import ProposalPayload

class ProposalNormalizer:
    @staticmethod
    def normalize(proposal_text: str, proposal_id: str) -> Optional[ProposalPayload]:
        """
        Extracts a structured ProposalPayload from potentially messy agent prose.
        Expects a JSON block inside the text.
        """
        # Try to find JSON block
        json_match = re.search(r"```json\s*(.*?)\s*```", proposal_text, re.DOTALL)
        if not json_match:
            # Try finding a raw { ... } block
            json_match = re.search(r"(\{.*?\})", proposal_text, re.DOTALL)
            
        if not json_match:
            return None
            
        try:
            data = json.loads(json_match.group(1))
            
            # Basic validation of required fields
            required = ["healthy_params", "schiz_params"]
            for field in required:
                if field not in data:
                    return None
            
            return ProposalPayload(
                proposal_id=data.get("proposal_id", proposal_id),
                seed_pair=data.get("seed_pair", 42),
                healthy_params=data["healthy_params"],
                schiz_params=data["schiz_params"],
                rationale=data.get("rationale", "")
            )
        except Exception:
            return None
