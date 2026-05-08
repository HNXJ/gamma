import os
import json
import hashlib
import argparse

def _parse_minimal_yaml(content: str) -> dict:
    """Minimal YAML parser specialized for the event_definition."""
    result = {"event_definition": {"components": {}}}

    event_id = None
    components = {}

    lines = content.split('\n')
    current_key = None
    current_val = []

    in_components = False

    for line in lines:
        if line.startswith('  event_id:'):
            event_id = line.split(':', 1)[1].strip()
        elif line.startswith('  components:'):
            in_components = True
        elif in_components and line.startswith('    A: |'):
            if current_key:
                components[current_key] = '\n'.join(current_val).strip()
            current_key = 'A'
            current_val = []
        elif in_components and line.startswith('    P0: |'):
            if current_key:
                components[current_key] = '\n'.join(current_val).strip()
            current_key = 'P0'
            current_val = []
        elif in_components and line.startswith('    B: |'):
            if current_key:
                components[current_key] = '\n'.join(current_val).strip()
            current_key = 'B'
            current_val = []
        elif in_components and current_key and not line.startswith(' ' * 6) and line.strip() != '':
            # End of a block and NOT starting a new known component
            components[current_key] = '\n'.join(current_val).strip()
            current_key = None
            if line.startswith('  turn_rule:') or line.startswith('  output_contract:'):
                in_components = False
        elif current_key and (line.startswith(' ' * 6) or line.strip() == ''):
            if line.startswith(' ' * 6):
                current_val.append(line[6:])
            else:
                current_val.append(line)

    if current_key:
        components[current_key] = '\n'.join(current_val).strip()

    result["event_definition"]["event_id"] = event_id
    result["event_definition"]["components"] = components

    return result

def load_event_definition(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return _parse_minimal_yaml(content)

def extract_components(event: dict) -> dict:
    return event.get("event_definition", {}).get("components", {})

def compose_prompt(components: dict, order: str, state_packet: dict | None = None) -> str:
    a_text = components.get("A", "")
    p_text = components.get("P0", "") if state_packet is None else str(state_packet)
    b_text = components.get("B", "")

    if order == "A_plus_P_plus_B":
        return f"# A_OBJECTIVE\n{a_text}\n\n# P_STATE\n{p_text}\n\n# B_RULES\n{b_text}"
    elif order == "B_plus_P_plus_A":
        return f"# B_RULES\n{b_text}\n\n# P_STATE\n{p_text}\n\n# A_OBJECTIVE\n{a_text}"
    else:
        raise ValueError(f"Unsupported order: {order}")

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def make_mock_process_call(event_path: str, output_dir: str, turn_index: int = 0, composition_order: str | None = None) -> dict:
    event = load_event_definition(event_path)
    components = extract_components(event)

    if composition_order is None:
        composition_order = "A_plus_P_plus_B"

    prompt = compose_prompt(components, composition_order)

    a_text = components.get("A", "")
    p_text = components.get("P0", "")
    b_text = components.get("B", "")

    a_sha256 = sha256_text(a_text)
    p_sha256 = sha256_text(p_text)
    b_sha256 = sha256_text(b_text)
    full_prompt_sha256 = sha256_text(prompt)

    response_text = "MOCK_RESPONSE_NOT_LIVE_EVIDENCE"
    response_sha256 = sha256_text(response_text)

    turn_record = {
        "event_id": event.get("event_definition", {}).get("event_id"),
        "turn_index": turn_index,
        "composition_order": composition_order,
        "components_used": ["B", "P", "A"] if composition_order == "B_plus_P_plus_A" else ["A", "P", "B"],
        "a_sha256": a_sha256,
        "p_sha256": p_sha256,
        "b_sha256": b_sha256,
        "full_prompt_sha256": full_prompt_sha256,
        "response_sha256": response_sha256,
        "truth_mode": "truth_safe_unverified",
        "truth_bearing_run": False,
        "mock_transport": True,
        "live_model_call": False,
        "secret_redaction_pass": True,
        "judge_verdict": "continue"
    }

    os.makedirs(output_dir, exist_ok=True)

    turn_path = os.path.join(output_dir, f"turn_{turn_index:04d}.json")
    with open(turn_path, 'w', encoding='utf-8') as f:
        json.dump(turn_record, f, indent=2)

    state_packet = {
        "packet_id": f"state_packet_{turn_index:04d}",
        "event_id": event.get("event_definition", {}).get("event_id"),
        "turn_index": turn_index,
        "composition_order": composition_order,
        "components_used": ["B", "P", "A"] if composition_order == "B_plus_P_plus_A" else ["A", "P", "B"],
        "prompt_hash": full_prompt_sha256,
        "full_prompt_sha256": full_prompt_sha256,
        "output_hash": response_sha256,
        "response_sha256": response_sha256,
        "judge_verdict": "continue",
        "truth_mode": "truth_safe_unverified",
        "truth_bearing_run": False,
        "mock_transport": True,
        "live_model_call": False,
        "status": "mock_state_packet_not_truth"
    }
    state_packet_path = os.path.join(output_dir, f"state_packet_{turn_index:04d}.json")
    with open(state_packet_path, 'w', encoding='utf-8') as f:
        json.dump(state_packet, f, indent=2)

    return turn_record

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--turn", type=int, default=0)
    parser.add_argument("--order", choices=["A_plus_P_plus_B", "B_plus_P_plus_A"], default=None)
    args = parser.parse_args()

    make_mock_process_call(args.event, args.out, args.turn, args.order)
    print(f"Mock execution completed for {args.event} -> {args.out}")
