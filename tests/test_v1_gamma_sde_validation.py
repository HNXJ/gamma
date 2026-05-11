import unittest
import json
import os
import tempfile
import shutil
from apps.v1_gamma_sde_app import V1GammaSDEOrchestrator
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.runtime_types import MissionContext

class TestV1GammaSDEValidation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.proposals_dir = os.path.join(self.test_dir, "data", "sde_proposals")
        os.makedirs(self.proposals_dir, exist_ok=True)

        # Mocking requirements
        self.registry = RuntimeRegistry(os.path.join(os.getcwd(), "context", "configs"))
        self.scheduler = InferenceScheduler()
        self.blackboard = Blackboard("Test Topic")
        self.mission_context = MissionContext(target_neuron_count=100, mission_topic="Gamma", patch_id="p1")

        self.orchestrator = V1GammaSDEOrchestrator(self.scheduler, self.registry, self.mission_context, self.blackboard)
        self.orchestrator.proposals_dir = self.proposals_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_emit_proposal_accepted(self):
        content = """
        Here is my proposal:
        ```json
        {
          "study_question": "Does N=100 converge?",
          "claim_type": "simulation_result",
          "intended_action": "run_python",
          "python_or_analysis_requirement": "none",
          "parameters_with_units": {},
          "expected_artifacts": [],
          "validation_gates": [],
          "next_handoff": "slot_02",
          "meta": {"neuron_count": 100},
          "proposal_id": "p_ok"
        }
        ```
        """
        await self.orchestrator._emit_proposal(1, content)

        latest_entry = self.blackboard.get_latest_entry()
        self.assertEqual(latest_entry.metadata.get("kind"), "proposal_acceptance")
        self.assertTrue(os.path.exists(os.path.join(self.proposals_dir, "p_ok.json")))

    async def test_emit_proposal_prose_drift(self):
        content = "I think we should look into the PV/SST interaction more deeply."
        await self.orchestrator._emit_proposal(1, content)

        latest_entry = self.blackboard.get_latest_entry()
        self.assertEqual(latest_entry.metadata.get("kind"), "drift_warning")
        self.assertEqual(latest_entry.metadata.get("reason"), "prose_only_yapping")

    async def test_emit_proposal_rubric_violation(self):
        content = """
        ```json
        {
          "study_question": "Violating rubric",
          "claim_type": "empirical_observation",
          "intended_action": "propose_only",
          "python_or_analysis_requirement": "none",
          "parameters_with_units": {},
          "expected_artifacts": [],
          "validation_gates": [],
          "next_handoff": "slot_02",
          "meta": {"neuron_count": 100}
        }
        ```
        """
        await self.orchestrator._emit_proposal(1, content)

        latest_entry = self.blackboard.get_latest_entry()
        self.assertEqual(latest_entry.metadata.get("kind"), "proposal_rejection")
        self.assertIn("Forbidden claim_type 'empirical_observation'", latest_entry.content)

if __name__ == "__main__":
    unittest.main()
