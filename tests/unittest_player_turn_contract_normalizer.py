import unittest
import json
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gamma_runtime.player_turn_contract_normalizer import PlayerTurnNormalizer

class TestPlayerTurnNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = PlayerTurnNormalizer()

    def test_canonical_stance_pass(self):
        raw = {"player_id": "p1", "stance_id": "scout", "truth_status": "truth_safe_unverified", "contribution": "working on JAXFNE"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["canonical_stance"], "scout")
        self.assertEqual(res["normalization_status"], "repaired")

    def test_player_name_suffix_stance(self):
        raw = {"player": "gemma_e4b.patchsmith", "stance_id": "noisy_label", "contribution": "JAXFNE"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["canonical_stance"], "patchsmith")
        self.assertTrue(any("Inferred stance" in w for w in res["warnings"]))

    def test_scientist_stance_repair(self):
        raw = {"player_id": "p1", "stance": "scientist_stance", "contribution": "JAXFNE"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["canonical_stance"], "scientist_scaffold")

    def test_ambiguous_stance_rejection(self):
        raw = {"player_id": "p1", "stance_id": "Gamma Labyrinth"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertTrue(any("Could not normalize stance" in e for e in res["errors"]))

    def test_missing_truth_status_default(self):
        raw = {"player_id": "p1", "stance_id": "scout"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["truth_status"], "truth_safe_unverified")

    def test_accepted_truth_rejection(self):
        raw = {"player_id": "p1", "stance_id": "scout", "truth_status": "accepted_truth"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertTrue(any("forbidden" in e for e in res["errors"]))

    def test_missing_validation_gate_warning(self):
        raw = {"player_id": "p1", "stance_id": "scout"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["validation_gate"], "missing_validation_gate_requires_repair")
        self.assertTrue(any("validation_gate" in w for w in res["warnings"]))

    def test_missing_expected_artifact_warning(self):
        raw = {"player_id": "p1", "stance_id": "scout"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["expected_artifact"], "missing_expected_artifact_requires_repair")

    def test_scaffold_result_boundary_insertion(self):
        raw = {"player_id": "p1", "stance_id": "scout"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["scaffold_vs_result_boundary"], "proposal_or_scaffold_only_until_execution_receipt")

    def test_biological_mechanism_claim_rejection(self):
        raw = {"player_id": "p1", "stance_id": "scout", "contribution": "Found a biological mechanism."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertTrue(any("Biological mechanism" in e for e in res["errors"]))

    def test_jaxfne_simulation_claim_rejection_without_receipt(self):
        raw = {"player_id": "p1", "stance_id": "scout", "contribution": "JAXFNE simulation result confirms X."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertTrue(any("simulation result" in e for e in res["errors"]))

    def test_n4_unlock_claim_rejection(self):
        raw = {"player_id": "p1", "stance_id": "scout", "contribution": "N=4 unlock achieved."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertTrue(any("N=4 unlock" in e for e in res["errors"]))

    def test_legacy_resource_request_conversion(self):
        raw = {"player_id": "p1", "stance_id": "scout", "resource_request_or_null": "5000 cycles"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["resource_requested"], "5000 cycles")

    def test_legacy_trade_offer_conversion(self):
        raw = {"player_id": "p1", "stance_id": "scout", "trade_offer_or_null": "tool_x"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["tool_used_or_requested"], "tool_x")

    def test_full_normalized_output_schema(self):
        raw = {
            "player_id": "p1",
            "stance_id": "scout",
            "current_objective": "test",
            "selected_action_type": "analysis",
            "validation_gate": "pass",
            "expected_artifact": "file.txt",
            "scaffold_vs_result_boundary": "scaffold",
            "truth_status": "truth_safe_unverified",
            "next_autonomous_step": "step",
            "contribution": "jaxfne"
        }
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "accepted")
        self.assertEqual(res["player_id"], "p1")
        self.assertEqual(res["canonical_stance"], "scout")
        self.assertEqual(res["current_objective"], "test")

    # --- Domain Guard Tests ---

    def test_valid_jaxfne_schema_validator(self):
        raw = {"player_id": "p1", "stance_id": "toolmaker", "contribution": "Creating a JAXFNE schema validator."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["domain_guard_status"], "on_mission")
        self.assertIn("jaxfne", res["on_mission_terms_detected"])
        self.assertIn("schema validator", res["on_mission_terms_detected"])

    def test_valid_jaxfne_mission_card(self):
        raw = {"player_id": "p1", "stance_id": "scientist_scaffold", "contribution": "Drafting a new mission card for computational neuroscience."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["domain_guard_status"], "on_mission")
        self.assertIn("mission card", res["on_mission_terms_detected"])
        self.assertIn("computational neuroscience", res["on_mission_terms_detected"])

    def test_valid_ei_scaffold_proposal(self):
        raw = {"player_id": "p1", "stance_id": "scientist_scaffold", "contribution": "E/I scaffold proposal"}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["domain_guard_status"], "on_mission")
        self.assertIn("e/i", res["on_mission_terms_detected"])

    def test_protein_folding_main_task_rejected(self):
        raw = {"player_id": "p1", "stance_id": "scientist_scaffold", "contribution": "I will model protein folding."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertEqual(res["domain_guard_status"], "rejected")
        self.assertIn("route_to_critic_judgelet_domain_correction", res["errors"])

    def test_enzyme_kinetics_main_task_rejected(self):
        raw = {"player_id": "p1", "stance_id": "scientist_scaffold", "contribution": "Evaluating enzyme kinetics."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertEqual(res["domain_guard_status"], "rejected")

    def test_molecular_docking_rejected(self):
        raw = {"player_id": "p1", "stance_id": "scientist_scaffold", "contribution": "Setting up molecular docking."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertEqual(res["domain_guard_status"], "rejected")

    def test_high_fidelity_simulation_rejected_without_mission_card(self):
        # In our normalizer logic, 'generic diffusion model' is off_mission. Let's trigger a drift ratio > 0.3.
        raw = {"player_id": "p1", "stance_id": "scientist_scaffold", "contribution": "Running generic diffusion model for high fidelity simulation."}
        res = self.normalizer.normalize(raw)
        self.assertEqual(res["normalization_status"], "rejected")
        self.assertEqual(res["domain_guard_status"], "rejected")

    def test_minor_force_field_mention_repaired(self):
        # We need a minor drift (e.g. 1 off mission term) + enough on mission terms to keep drift_ratio <= 0.3
        raw = {"player_id": "p1", "stance_id": "patchsmith", "contribution": "Adding unrelated force field to the JAXFNE schema validator tutorial output."}
        res = self.normalizer.normalize(raw)
        # on mission: jaxfne, schema validator, tutorial output (3)
        # off mission: unrelated force field (1)
        # ratio: 1/4 = 0.25 <= 0.3 -> repaired
        self.assertEqual(res["normalization_status"], "repaired")
        self.assertEqual(res["domain_guard_status"], "repaired")
        self.assertTrue(any("Domain drift warning" in w for w in res["warnings"]))

    def test_domain_guard_fields_in_output(self):
        raw = {"player_id": "p1", "stance_id": "scout"}
        res = self.normalizer.normalize(raw)
        self.assertIn("domain_guard_status", res)
        self.assertIn("domain_guard_warnings", res)
        self.assertIn("domain_guard_errors", res)
        self.assertIn("off_mission_terms_detected", res)
        self.assertIn("on_mission_terms_detected", res)
        self.assertIn("active_domain", res)

    def test_missing_config_safe_defaults(self):
        # Test with missing file
        normalizer = PlayerTurnNormalizer(domain_config_path="missing_file.json")
        raw = {"player_id": "p1", "stance_id": "scout", "contribution": "jaxfne"}
        res = normalizer.normalize(raw)
        self.assertEqual(res["active_domain"], "jaxfne_computational_neuroscience_biophysics")
        self.assertEqual(res["domain_guard_status"], "on_mission")

    def test_config_injection(self):
        custom_config = {
            "active_domain": "custom",
            "allowed_terms": ["custom_allow"],
            "off_mission_terms": ["custom_reject"],
            "hard_reject_terms": ["custom_reject"],
            "max_off_mission_terms_before_reject": 1,
            "max_drift_ratio_before_reject": 0.5
        }
        normalizer = PlayerTurnNormalizer(domain_config=custom_config)
        raw = {"player_id": "p1", "stance_id": "scout", "contribution": "custom_allow custom_reject"}
        res = normalizer.normalize(raw)
        self.assertEqual(res["domain_guard_status"], "rejected")

if __name__ == '__main__':
    unittest.main()
