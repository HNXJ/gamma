import os
import json
import re

class PlayerTurnNormalizer:
    CANONICAL_STANCES = [
        'scout', 'patchsmith', 'toolmaker', 'trader', 'archivist',
        'scientist_scaffold', 'critic_judgelet', 'sandbox_curator'
    ]

    STANCE_MAP = {
        'data/literature analysis': 'scout',
        'scientific_runtime_participant': 'critic_judgelet',
        'scientist_stance': 'scientist_scaffold',
        'science_scaffold': 'scientist_scaffold',
        'critic': 'critic_judgelet',
        'judgelet': 'critic_judgelet',
        'sandbox': 'sandbox_curator',
        'curator': 'sandbox_curator'
    }

    ACTION_MAP = {
        'propose_tool': 'tool_improvement',
        'resource_request': 'request_resource',
        'patch_proposal': 'propose_patch',
        'trade_offer': 'trade',
        'scaffold': 'scaffold',
        'critique': 'critique',
        'archival': 'archive'
    }

    def __init__(self, domain_config_path="context/configs/player_turn_domain_guard.json", domain_config=None):
        if domain_config is not None:
            self.domain_config = domain_config
        else:
            try:
                with open(domain_config_path, "r") as f:
                    self.domain_config = json.load(f)
            except Exception:
                self.domain_config = {
                    "active_domain": "jaxfne_computational_neuroscience_biophysics",
                    "allowed_terms": [
                        "jaxfne", "schema validator", "type validator", "shape validator",
                        "tutorial output", "mission card", "scaffold", "receipt", "artifact",
                        "computational neuroscience", "biophysical modeling", "neural",
                        "e/i", "omission", "predictive coding", "spike-field", "sparse spiking",
                        "field modulation", "harness", "tool market"
                    ],
                    "off_mission_terms": [
                        "protein", "protein folding", "folding", "enzyme", "enzyme kinetics",
                        "molecular docking", "molecular dynamics", "ligand", "ligand binding",
                        "generic diffusion model", "unrelated force field", "force field refinement"
                    ],
                    "hard_reject_terms": [
                        "protein folding", "enzyme kinetics", "molecular docking", "ligand binding"
                    ],
                    "max_off_mission_terms_before_reject": 2,
                    "max_drift_ratio_before_reject": 0.3,
                    "truth_status": "truth_safe_unverified"
                }

    def normalize(self, raw_turn):
        normalized = {
            "player_id": raw_turn.get("player", raw_turn.get("player_id", "unknown")),
            "canonical_stance": "",
            "current_objective": raw_turn.get("current_objective", ""),
            "selected_action_type": "",
            "tool_used_or_requested": raw_turn.get("tool_used_or_requested", ""),
            "resource_requested": raw_turn.get("resource_requested", ""),
            "validation_gate": "",
            "expected_artifact": "",
            "scaffold_vs_result_boundary": "",
            "truth_status": raw_turn.get("truth_status", "truth_safe_unverified"),
            "next_autonomous_step": "",
            "normalization_status": "accepted",
            "warnings": [],
            "errors": [],
            "source_fields": list(raw_turn.keys()),

            # Domain Guard Fields
            "domain_guard_status": "not_configured",
            "domain_guard_warnings": [],
            "domain_guard_errors": [],
            "off_mission_terms_detected": [],
            "on_mission_terms_detected": [],
            "active_domain": self.domain_config.get("active_domain", "jaxfne_computational_neuroscience_biophysics")
        }

        # Stance Normalization
        raw_stance = raw_turn.get("stance", raw_turn.get("stance_id", ""))
        player_id = normalized["player_id"]

        stance = ""
        if raw_stance in self.CANONICAL_STANCES:
            stance = raw_stance
        elif raw_stance in self.STANCE_MAP:
            stance = self.STANCE_MAP[raw_stance]
            normalized["warnings"].append(f"Mapped legacy stance '{raw_stance}' to '{stance}'")
        else:
            # Check player_id suffix
            for s in self.CANONICAL_STANCES:
                if player_id.endswith("." + s):
                    stance = s
                    normalized["warnings"].append(f"Inferred stance '{stance}' from player_id suffix")
                    break

        if not stance:
            normalized["normalization_status"] = "rejected"
            normalized["errors"].append(f"Could not normalize stance '{raw_stance}'")
        else:
            normalized["canonical_stance"] = stance

        # Domain Guard Check
        if self.domain_config:
            content_to_check = str(raw_turn).lower()

            allowed = [t.lower() for t in self.domain_config.get("allowed_terms", [])]
            off_mission = [t.lower() for t in self.domain_config.get("off_mission_terms", [])]
            hard_reject = [t.lower() for t in self.domain_config.get("hard_reject_terms", [])]

            found_on_mission = []
            for t in allowed:
                if t in content_to_check:
                    found_on_mission.append(t)

            found_off_mission = []
            for t in off_mission:
                if t in content_to_check:
                    found_off_mission.append(t)

            normalized["on_mission_terms_detected"] = found_on_mission
            normalized["off_mission_terms_detected"] = found_off_mission

            total_terms = len(found_on_mission) + len(found_off_mission)
            drift_ratio = len(found_off_mission) / total_terms if total_terms > 0 else 0

            # Rejection logic
            rejected = False
            for t in hard_reject:
                if t in content_to_check:
                    rejected = True
                    normalized["domain_guard_errors"].append(f"Hard reject term found: {t}")

            max_off = self.domain_config.get("max_off_mission_terms_before_reject", 2)
            if len(found_off_mission) > max_off:
                rejected = True
                normalized["domain_guard_errors"].append(f"Exceeded max off-mission terms ({len(found_off_mission)} > {max_off})")

            max_ratio = self.domain_config.get("max_drift_ratio_before_reject", 0.3)
            if drift_ratio > max_ratio and len(found_off_mission) > 0:
                rejected = True
                normalized["domain_guard_errors"].append(f"Exceeded max drift ratio ({drift_ratio:.2f} > {max_ratio})")

            if rejected:
                normalized["domain_guard_status"] = "rejected"
                normalized["normalization_status"] = "rejected"
                normalized["errors"].append("route_to_critic_judgelet_domain_correction")
            elif len(found_off_mission) > 0:
                # Repair logic for minor drift
                normalized["domain_guard_status"] = "repaired"
                normalized["normalization_status"] = "repaired"
                normalized["domain_guard_warnings"].append("Minor domain drift detected.")
                normalized["warnings"].append("Domain drift warning: refocus on JAXFNE computational neuroscience.")
            else:
                normalized["domain_guard_status"] = "on_mission"

        # Truth Rules
        if normalized["truth_status"] == "accepted_truth":
            normalized["normalization_status"] = "rejected"
            normalized["errors"].append("truth_status 'accepted_truth' is forbidden")

        contribution = str(raw_turn.get("contribution", ""))
        if re.search(r"biological|mechanism|neuron|synapse", contribution, re.I):
             normalized["normalization_status"] = "rejected"
             normalized["errors"].append("Biological mechanism claims are forbidden")

        if re.search(r"simulation result|JAXFNE result", contribution, re.I) and "receipt" not in contribution.lower():
             normalized["normalization_status"] = "rejected"
             normalized["errors"].append("JAXFNE simulation result claims without receipt are forbidden")

        if re.search(r"N=3 closure|N=4 unlock", contribution, re.I):
             normalized["normalization_status"] = "rejected"
             normalized["errors"].append("N=3 closure or N=4 unlock claims are forbidden")

        # Action Type Normalization
        raw_action = raw_turn.get("action_type", "")
        if raw_action in self.ACTION_MAP:
            normalized["selected_action_type"] = self.ACTION_MAP[raw_action]
        else:
            normalized["selected_action_type"] = raw_action

        # Field Repair
        if not raw_turn.get("validation_gate"):
            normalized["validation_gate"] = "missing_validation_gate_requires_repair"
            normalized["warnings"].append("Missing validation_gate")
        else:
            normalized["validation_gate"] = raw_turn["validation_gate"]

        if not raw_turn.get("expected_artifact"):
            normalized["expected_artifact"] = "missing_expected_artifact_requires_repair"
            normalized["warnings"].append("Missing expected_artifact")
        else:
            normalized["expected_artifact"] = raw_turn["expected_artifact"]

        if not raw_turn.get("scaffold_vs_result_boundary"):
            normalized["scaffold_vs_result_boundary"] = "proposal_or_scaffold_only_until_execution_receipt"
            normalized["warnings"].append("Missing scaffold_vs_result_boundary")
        else:
            normalized["scaffold_vs_result_boundary"] = raw_turn["scaffold_vs_result_boundary"]

        # Next Autonomous Step Inference
        if not raw_turn.get("next_autonomous_step"):
            action = normalized["selected_action_type"]
            if stance == 'scout': normalized["next_autonomous_step"] = 'identify next blocker'
            elif stance == 'patchsmith': normalized["next_autonomous_step"] = 'draft bounded patch'
            elif stance == 'toolmaker': normalized["next_autonomous_step"] = 'define validator/tool artifact'
            elif stance == 'trader': normalized["next_autonomous_step"] = 'propose bounded trade'
            elif stance == 'archivist': normalized["next_autonomous_step"] = 'record receipt fields'
            elif stance == 'scientist_scaffold': normalized["next_autonomous_step"] = 'write mission card'
            elif stance == 'critic_judgelet': normalized["next_autonomous_step"] = 'audit truth boundary'
            elif stance == 'sandbox_curator': normalized["next_autonomous_step"] = 'request bounded resource'
            else: normalized["next_autonomous_step"] = 'await next directive'
            normalized["warnings"].append("Inferred next_autonomous_step")
        else:
            normalized["next_autonomous_step"] = raw_turn["next_autonomous_step"]

        # Legacy conversions
        if "resource_request_or_null" in raw_turn and raw_turn["resource_request_or_null"]:
            normalized["resource_requested"] = str(raw_turn["resource_request_or_null"])
        if "trade_offer_or_null" in raw_turn and raw_turn["trade_offer_or_null"]:
            normalized["tool_used_or_requested"] = str(raw_turn["trade_offer_or_null"])

        if normalized["normalization_status"] == "accepted" and normalized["warnings"]:
            normalized["normalization_status"] = "repaired"

        return normalized
