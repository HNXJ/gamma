import unittest
import os
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.blackboard import Blackboard
from apps.council_app import CouncilOrchestrator
from gamma_runtime.runtime_types import AgentSpec

class TestModelKeyResolution(unittest.TestCase):
    def test_gemma4_parallel_resolution(self):
        # Use the real project context
        root = os.getcwd()
        config_path = os.path.join(root, "context", "configs")
        registry = RuntimeRegistry(config_path)
        scheduler = InferenceScheduler()
        blackboard = Blackboard("Resolution Test")
        orchestrator = CouncilOrchestrator(scheduler, registry, blackboard)

        # Manually construct an agent spec that uses gemma4-parallel
        agent = AgentSpec(
            agent_id="v1_gamma_proponent",
            role="Mechanistic proposer",
            model_key="gemma4-parallel",
            system_prompt="Test"
        )

        request = orchestrator._build_request(agent)

        # ASSERTIONS
        # 1. Internal model_key is preserved
        self.assertEqual(request.model_key, "gemma4-parallel")
        # 2. Outbound model_id is resolved to canonical name
        self.assertEqual(request.model_id, "gemma-4-e4b-it-mlx")
        # 3. No suffix is synthesized
        self.assertNotIn(":", request.model_id)

if __name__ == "__main__":
    unittest.main()
