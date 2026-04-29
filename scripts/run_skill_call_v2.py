import requests
import json
import sys
import os

url = "http://localhost:1234/v1/chat/completions"
model = "gemma-4-e4b-it-mxfp8"

system_prompt = """You are the V1 Gamma Proponent. Your goal is to find stable schizophrenia-like gamma pathology parameters.

SKILL ARCHITECTURE MANDATE:
You MUST follow the Paper-Anchored Skill Architecture (see skills/SKILLS.md).

AVAILABLE SKILLS (from skills_lib.py):
- skill_target_natural_frequency(psd, freqs)
"""

user_prompt = "I have a PSD result. freqs = [10, 20, 30, 40, 50], psd = [0.1, 0.5, 2.5, 0.4, 0.1]. Use the registered skill to find the peak frequency and tell me the result."

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

print(f"--- Agent: v1_gamma_proponent ---")
response = requests.post(url, json=payload).json()
tool_call = response['choices'][0]['message']['tool_calls'][0]
print(f"TOOL CALL: {tool_call['function']['name']}({tool_call['function']['arguments']})")

# Mocking the TOOL RESULT execution
import sys; sys.path.append("/Users/HN/MLLM/gamma/src"); from gamma_runtime.skills_lib import skill_target_natural_frequency
args = json.loads(tool_call['function']['arguments'])
result = skill_target_natural_frequency(**args)
print(f"TOOL RESULT: {result}")

# Second call to get the final response
payload['messages'].append(response['choices'][0]['message'])
payload['messages'].append({
    "role": "tool",
    "tool_call_id": tool_call['id'],
    "name": tool_call['function']['name'],
    "content": json.dumps(result)
})

final_response = requests.post(url, json=payload).json()
print(f"FINAL RESPONSE: {final_response['choices'][0]['message']['content']}")
