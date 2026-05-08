import os
import tempfile
import json
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
        prompt = compose_prompt(components, "A_plus_P_plus_B")
        expected_prompt = "# A_OBJECTIVE\nTest Role\n\n# P_STATE\nTest State\n\n# B_RULES\nTest Rules"
        assert prompt == expected_prompt

        # 4. hashes are deterministic
        hash1 = sha256_text(prompt)
        hash2 = sha256_text(prompt)
        assert hash1 == hash2

        # 5/6. mock process writes turn and state packet
        out_dir = os.path.join(tmpdir, "out")
        make_mock_process_call(yaml_path, out_dir, turn_index=0)

        assert os.path.exists(os.path.join(out_dir, "turn_0000.json"))
        assert os.path.exists(os.path.join(out_dir, "state_packet_0000.json"))

        with open(os.path.join(out_dir, "turn_0000.json"), encoding="utf-8") as f:
            turn_data = json.load(f)

        # 7, 8, 9, 10
        assert turn_data["truth_mode"] == "truth_safe_unverified"
        assert turn_data["mock_transport"] is True
        assert turn_data["live_model_call"] is False
        assert "truth_value" not in turn_data
