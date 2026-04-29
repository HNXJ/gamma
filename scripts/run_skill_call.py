import requests
import json

url = "http://localhost:1234/v1/chat/completions"
model = "gemma-4-e4b-it-mxfp8"

system_prompt = """You are the V1 Gamma Proponent. Your goal is to find stable schizophrenia-like gamma pathology parameters.

SKILL ARCHITECTURE MANDATE:
You MUST follow the Paper-Anchored Skill Architecture (see skills/SKILLS.md). Any code that produces validated artifacts should be proposed as a reusable skill skeleton under the Promotion Rule.

AVAILABLE SKILLS (from skills_lib.py):
- skill_psd_band_report(psd, freqs)
- skill_target_natural_frequency(psd, freqs)
- skill_target_synchronization_index(kappa, T=100, N=10)
"""

user_prompt = "I have the following PSD data from a simulation: freqs = [10, 20, 30, 40, 50], psd = [0.1, 0.5, 2.5, 0.4, 0.1]. Use the registered skill 'skill_target_natural_frequency' to identify the peak oscillation frequency."

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "skill_target_natural_frequency",
                "description": "Identifies peak frequency and power in a PSD array.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "psd": {"type": "array", "items": {"type": "number"}},
                        "freqs": {"type": "array", "items": {"type": "number"}}
                    },
                    "required": ["psd", "freqs"]
                }
            }
        }
    ],
    "tool_choice": "auto"
}

print("--- Executing Skill Use Council Call ---")
response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
