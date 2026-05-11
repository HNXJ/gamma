import unittest
from apps.council_app import CouncilOrchestrator
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.runtime_types import AgentSpec
import os

class TestScientificWorkUnitPrompt(unittest.TestCase):
    def test_rubric_injection(self):
        # Mocking requirements for CouncilOrchestrator
        registry = RuntimeRegistry(os.path.join(os.getcwd(), "context", "configs"))
        scheduler = InferenceScheduler()
        blackboard = Blackboard("Test Topic")
        orchestrator = CouncilOrchestrator(scheduler, registry, blackboard)

        agent = AgentSpec(
            agent_id="test_agent",
            role="tester",
            model_key="gemma4-parallel",
            system_prompt="You are a tester.",
            generation={"max_tokens": 100}
        )

        request = orchestrator._build_request(agent)
        prompt = request.messages[1]["content"]

        self.assertIn("--- SCIENTIFIC WORK-UNIT RUBRIC ---", prompt)
        self.assertIn("study_question", prompt)
        self.assertIn("claim_type", prompt)
        self.assertIn("intended_action", prompt)
        self.assertIn("python_or_analysis_requirement", prompt)
        self.assertIn("propose_only", prompt)

if __name__ == "__main__":
    unittest.main()
