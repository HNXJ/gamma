import os
import json
from typing import List, Dict, Any

class RulesResolver:
    def __init__(self, patches_dir: str):
        self.patches_dir = patches_dir

    def resolve_rules(self, state: Dict[str, Any], active_patches: List[str]) -> Dict[str, Any]:
        rules = {
            "unlocks": [],
            "active_rules": [],
            "features": {},
            "allowed_actions": []
        }
        
        # Default rules if no patches
        rules["features"]["neuron_count"] = 10
        rules["features"]["composition"] = {"E": 7, "PV": 2, "SST": 1}
        
        for patch_id in sorted(active_patches):
            patch_path = os.path.join(self.patches_dir, f"{patch_id}.json")
            if os.path.exists(patch_path):
                with open(patch_path, 'r') as f:
                    patch = json.load(f)
                    self._apply_patch(rules, patch)
                    
        return rules

    def _apply_patch(self, rules: Dict[str, Any], patch: Dict[str, Any]):
        changes = patch.get('changes', {})
        
        # Merge Unlocks
        rules["unlocks"].extend(changes.get('unlocks', []))
        
        # Merge Rules
        rules["active_rules"].extend(changes.get('rules', []))
        
        # Update Features
        rules["features"].update(changes.get('features', {}))
        
        # Merge Allowed Actions
        rules["allowed_actions"].extend(changes.get('allowed_actions', []))

