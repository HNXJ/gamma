
import json
import re
from typing import Dict, Any

def parse_proposal_text(text: str) -> Dict[str, Any]:
    # 1. Try to find fenced JSON blocks
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        try:
            return {"status": "success", "data": json.loads(fenced_match.group(1))}
        except json.JSONDecodeError as e:
            return {"status": "failed", "error": f"JSONDecodeError in fenced block: {str(e)}"}
            
    # 2. Try to find anything that looks like a JSON object
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        try:
            # Try to clean it up if there are multiple objects (take the first one or the one with parameters)
            # For simplicity, we take the largest match or first match.
            return {"status": "success", "data": json.loads(json_match.group(1))}
        except json.JSONDecodeError as e:
            return {"status": "failed", "error": f"JSONDecodeError in text: {str(e)}"}
            
    return {"status": "failed", "error": "No JSON object found in proposal text"}

def extract_parameters(proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    # 4. Look for a top-level parameters object first
    params = proposal_data.get("parameters", proposal_data)
    
    # 5. Extract plausible conductance keys
    valid_keys = {
        "gmax", "gNa_gmax", "gNa", "gNa_bar", "gK", "gLeak", 
        "gCa", "gM", "gA", "gH", "gK_bar", "gL", "g_leak",
        "mse", "mse_estimate"
    }
    
    extracted = {k: v for k, v in params.items() if k in valid_keys and isinstance(v, (int, float))}
    return extracted

# Test cases
test_cases = [
    {
        "name": "Fenced JSON",
        "text": "I propose these parameters:\n```json\n{\"parameters\": {\"gmax\": 0.45, \"mse\": 0.01}}\n```",
        "expected": {"gmax": 0.45, "mse": 0.01}
    },
    {
        "name": "Raw JSON",
        "text": "{\"parameters\": {\"gNa\": 0.12}, \"mse\": 0.04}",
        "expected": {"gNa": 0.12} # parameters object takes precedence
    },
    {
        "name": "Missing parameters object",
        "text": "The values are {\"gLeak\": 0.001, \"mse\": 0.02}.",
        "expected": {"gLeak": 0.001, "mse": 0.02}
    },
    {
        "name": "Malformed",
        "text": "I propose gmax = 0.42",
        "expected_status": "failed"
    },
    {
        "name": "Empty parameters",
        "text": "{\"parameters\": {}}",
        "expected": {}
    }
]

for case in test_cases:
    print(f"Testing: {case['name']}")
    res = parse_proposal_text(case["text"])
    if res["status"] == "success":
        params = extract_parameters(res["data"])
        print(f"  Extracted: {params}")
        if "expected" in case:
            assert params == case["expected"], f"Expected {case['expected']}, got {params}"
    else:
        print(f"  Failed: {res['error']}")
        if "expected_status" in case:
            assert res["status"] == case["expected_status"]
    print("-" * 20)

print("All tests passed!")
