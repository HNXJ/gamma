import unittest
import json
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from src.gamma_runtime.player_turn_contract_normalizer import PlayerTurnNormalizer
from scripts.live_game_loop_32_stances import ContinuousWorld

class TestLiveGameLoopNormalizerIntegration(unittest.TestCase):
    def setUp(self):
        self.output_dir = "tests/test_output_integration"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Mocking the LMSInterface and dependencies
        with patch('scripts.live_game_loop_32_stances.LMSInterface') as MockLMS:
            self.world = ContinuousWorld(resume_dir=None)
            self.world.output_dir = self.output_dir
            self.world.enable_normalizer = True
            self.world.normalizer = PlayerTurnNormalizer()

    def test_normalization_integration(self):
        # Sample raw turn that should be repaired
        raw_turn = {
            "player_id": "gemma_e4b.scout",
            "stance_id": "data/literature analysis",
            "action_type": "analysis",
            "contribution": "Reviewing literature.",
            "truth_status": "truth_safe_unverified"
        }

        # Mock completion response
        mock_res = MagicMock()
        mock_res.success = True
        mock_res.content = json.dumps(raw_turn)

        player = self.world.players[0]
        p_id = player["player_id"]
        turn_id = self.world.state["current_turn"]

        # Manually trigger the normalization logic as it would be in run_cycle
        content = mock_res.content.strip()
        json_str = content.replace("```json", "").replace("```", "").strip()
        raw_data = json.loads(json_str)
        normalized = self.world.normalizer.normalize(raw_data)

        # Verify normalization
        self.assertEqual(normalized["canonical_stance"], "scout")
        self.assertEqual(normalized["normalization_status"], "repaired")

        # Simulate writing to logs
        norm_path = os.path.join(self.output_dir, "normalized_turns.jsonl")
        with open(norm_path, "a") as f:
            f.write(json.dumps({"turn_id": turn_id, "player_id": p_id, "normalized": normalized}) + "\n")

        self.assertTrue(os.path.exists(norm_path))
        with open(norm_path, "r") as f:
            line = json.loads(f.readline())
            self.assertEqual(line["normalized"]["canonical_stance"], "scout")

    def test_rejection_integration(self):
        # Sample raw turn that should be rejected (biological claim)
        raw_turn = {
            "player_id": "gemma_e4b.scout",
            "stance_id": "scout",
            "action_type": "analysis",
            "contribution": "Found biological mechanism for memory.",
            "truth_status": "truth_safe_unverified"
        }

        raw_data = raw_turn
        normalized = self.world.normalizer.normalize(raw_data)

        self.assertEqual(normalized["normalization_status"], "rejected")

        reject_path = os.path.join(self.output_dir, "rejected_turns.jsonl")
        if normalized["normalization_status"] == "rejected":
            with open(reject_path, "a") as f:
                f.write(json.dumps({"player_id": "test_p", "errors": normalized["errors"]}) + "\n")

        self.assertTrue(os.path.exists(reject_path))
        with open(reject_path, "r") as f:
            line = json.loads(f.readline())
            self.assertIn("Biological mechanism", line["errors"][0])

if __name__ == '__main__':
    unittest.main()
