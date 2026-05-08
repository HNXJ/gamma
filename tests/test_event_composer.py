import os
import tempfile
import json
import hashlib
import pytest
from gamma_runtime.event_composer import (
    load_event_definition,
    extract_components,
    compose_prompt,
    sha256_text,
    make_mock_process_call
)

def test_event_composer():
    yaml_content = """event_definition:
  event_id: test_event_id
  components:
    A: |
      Test Role
    P0: |
      Test State
    B: |
      Test Rules
  turn_rule:
    prompt_n: A + P(n) + B
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "test_event.yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        # 1. load event YAML
        event = load_event_definition(yaml_path)
        assert event["event_definition"]["event_id"] == "test_event_id"

        # 2. extract A/P0/B
        components = extract_components(event)
        assert components["A"] == "Test Role"
        assert components["P0"] == "Test State"
        assert components["B"] == "Test Rules"

        # 3. composes in order A, P, B
        prompt_apb = compose_prompt(components, "A_plus_P_plus_B")
        expected_apb = "# A_OBJECTIVE\nTest Role\n\n# P_STATE\nTest State\n\n# B_RULES\nTest Rules"
        assert prompt_apb == expected_apb

        # 3b. composes in order B, P, A
        prompt_bpa = compose_prompt(components, "B_plus_P_plus_A")
        expected_bpa = "# B_RULES\nTest Rules\n\n# P_STATE\nTest State\n\n# A_OBJECTIVE\nTest Role"
        assert prompt_bpa == expected_bpa

        # 4. hashes are deterministic
        hash1 = sha256_text(prompt_apb)
        hash2 = sha256_text(prompt_apb)
        assert hash1 == hash2

        # 5/6. mock process writes turn and state packet (APB)
        out_dir_apb = os.path.join(tmpdir, "out_apb")
        make_mock_process_call(yaml_path, out_dir_apb, turn_index=0, composition_order="A_plus_P_plus_B")

        assert os.path.exists(os.path.join(out_dir_apb, "turn_0000.json"))
        with open(os.path.join(out_dir_apb, "turn_0000.json"), encoding="utf-8") as f:
            turn_apb = json.load(f)
        assert turn_apb["composition_order"] == "A_plus_P_plus_B"
        assert turn_apb["components_used"] == ["A", "P", "B"]

        # State packet verification (APB)
        with open(os.path.join(out_dir_apb, "state_packet_0000.json"), encoding="utf-8") as f:
            state_apb = json.load(f)
        assert state_apb["composition_order"] == "A_plus_P_plus_B"
        assert state_apb["components_used"] == ["A", "P", "B"]
        assert "prompt_hash" in state_apb
        assert "output_hash" in state_apb

        # 5/6b. mock process writes turn and state packet (BPA)
        out_dir_bpa = os.path.join(tmpdir, "out_bpa")
        make_mock_process_call(yaml_path, out_dir_bpa, turn_index=0, composition_order="B_plus_P_plus_A")

        assert os.path.exists(os.path.join(out_dir_bpa, "turn_0000.json"))
        with open(os.path.join(out_dir_bpa, "turn_0000.json"), encoding="utf-8") as f:
            turn_bpa = json.load(f)
        assert turn_bpa["composition_order"] == "B_plus_P_plus_A"
        assert turn_bpa["components_used"] == ["B", "P", "A"]

        # State packet verification (BPA)
        with open(os.path.join(out_dir_bpa, "state_packet_0000.json"), encoding="utf-8") as f:
            state_bpa = json.load(f)
        assert state_bpa["composition_order"] == "B_plus_P_plus_A"
        assert state_bpa["components_used"] == ["B", "P", "A"]

        # Verify hashes differ
        apb_hash = hashlib.sha256(json.dumps(state_apb, sort_keys=True).encode()).hexdigest()
        bpa_hash = hashlib.sha256(json.dumps(state_bpa, sort_keys=True).encode()).hexdigest()
        assert apb_hash != bpa_hash

        # 7, 8, 9, 10
        for data in [turn_apb, turn_bpa, state_apb, state_bpa]:
            assert data["truth_mode"] == "truth_safe_unverified"
            assert data["mock_transport"] is True
            assert data["live_model_call"] is False
            assert "truth_value" not in data

        # 11. Unsupported order
        with pytest.raises(ValueError, match="Unsupported order"):
            compose_prompt(components, "INVALID_ORDER")
