import unittest
import os
import json
import tempfile
import shutil
from gamma_runtime.lms_8slot_harness import LMS8SlotHarness
from gamma_runtime.lms_9slot_verify import SLOTS

class TestLMSModelCanonicalization(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_lms_8slot_harness_canonical_ids(self):
        harness = LMS8SlotHarness(self.test_dir)
        manifest = harness.generate_manifest()

        for i, req in enumerate(manifest):
            model = req['model']
            # Proof: No :N suffix is synthesized
            self.assertEqual(model, 'gemma-4-e4b-it-mlx', f"Slot {i} should use canonical ID")
            self.assertNotIn(':', model, f"Slot {i} model ID should not contain a suffix")

    def test_lms_9slot_verify_canonical_ids(self):
        for slot_id, conf in SLOTS.items():
            model = conf['model']
            if 'player_slot_01' in slot_id or 'player_slot_02' in slot_id or \
               'player_slot_03' in slot_id or 'player_slot_04' in slot_id or \
               'player_slot_05' in slot_id or 'player_slot_06' in slot_id:
                self.assertEqual(model, 'gemma-4-e4b-it-mlx', f"{slot_id} should use canonical ID")

            # General rule: No ordinal suffixes like :2, :3, :4, :5, :8
            self.assertFalse(any(model.endswith(f":{n}") for n in range(2, 10)),
                             f"{slot_id} model ID {model} should not have ordinal suffix")

if __name__ == "__main__":
    unittest.main()
