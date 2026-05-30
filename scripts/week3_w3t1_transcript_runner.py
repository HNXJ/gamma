import urllib.request
import json
import os

MODEL_ID = "gemma-4-26b-a4b-it"
BACKEND_URL = "http://127.0.0.1:1234/v1/chat/completions"
OUTPUT_DIR = r"D:\workspace\gemini-gamma-labyrinth\repos\gamma\outputs\tournament\week3_w3t1_10_turn_transcript"
TRANSCRIPT_PATH = os.path.join(OUTPUT_DIR, "transcript.md")

HARNESS_ID = "gamma_week3_w3t1_harness_01"
PLAYER_ID = "gamma_week3_w3t1_player_01"
SESSION_ID = "gamma_week3_w3t1_session_01"

# Grounding Context from Week 2/3
WORLD_STATE = """
Week 2 Closure: WEEK2_CLOSED_GROUNDED_AUDIT_EVIDENCE_ACCEPTED
Commit: f892d480a8548d2efc24080f2192917ce463996f

Confirmed Facts:
- JAXFNE Source Version: 0.3.14 (pyproject.toml).
- Import Status: JAXFNE import PASS in inventory root.
- Jaxley: ABSENT (ModuleNotFoundError).
- Placeholder Boundaries: jaxfne/bridges.py is a scaffold with NotImplementedError placeholders.
- Admitted Model: gemma-4-26b-a4b-it (16-agent concurrency verified).

Week 3 Implementation Gate:
Theme: Hardening architectural foundations (interfaces, validation, reporting).
W3-T1: Jaxley Optional Boundary and Import Diagnostics
Target Files: jaxfne/bridges.py, jaxfne/__init__.py
Scope: Enhance require_jaxley() and similar guards for unified, version-aware import error messages.
Validation: python -c "import jaxfne; jaxfne.bridges.require_jaxley()" must fail loudly.
"""

TURN_PROMPTS = [
    "Turn 1: Player admission. Acknowledge your harness, truth mode (truth_safe_unverified), and non-scope (no biology, no installation, no Truth mutation).",
    "Turn 2: Summarize the current world state based on the provided Week 2/3 context.",
    "Turn 3: Identify the specific target files for W3-T1 (Jaxley Optional Boundary and Import Diagnostics) and the type of diagnostics needed.",
    "Turn 4: Propose exact safe shell commands to verify Jaxley/JAXFNE import status without installing anything.",
    "Turn 5: Review the architectural requirements for the optional-dependency boundary and identify potential failure modes (e.g., silent failure vs loud crash).",
    "Turn 6: Propose 'placeholder-fails-loudly' criteria for Jaxley-dependent code paths (specifically in jaxfne/bridges.py) when the library is absent.",
    "Turn 7: Draft the validation criteria for W3-T1 success. Do not implement code, just define the expected verifiable behavior.",
    "Turn 8: Identify risks, stop conditions, and required artifacts for W3-T1 completion.",
    "Turn 9: Produce a bounded W3-T1 worker handoff summary for the next implementation agent.",
    "Turn 10: Return your final self-report with a decision: READY_FOR_W3_T1_IMPLEMENTATION_WORKER, REVISE_W3_T1_GATE, or BLOCKED_W3_T1."
]

def call_gemma(messages):
    data = json.dumps({
        'model': MODEL_ID,
        'messages': messages,
        'max_tokens': 1024,
        'temperature': 0
    }).encode('utf-8')
    req = urllib.request.Request(BACKEND_URL, data=data, headers={'Content-Type': 'application/json'})
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    return result['choices'][0]['message']['content']

def run_transcript():
    system_prompt = (
        f"You are {PLAYER_ID} in Gamma Labyrinth. Harness: {HARNESS_ID}. Session: {SESSION_ID}. "
        "You follow truth_safe_unverified doctrine. No biology, no installation, no Truth mutation.\n\n"
        f"WORLD STATE CONTEXT:\n{WORLD_STATE}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    transcript = f"# Gamma Labyrinth Transcript: Week 3 W3-T1 Planning\n\n"
    transcript += f"**Player ID:** {PLAYER_ID}\n"
    transcript += f"**Session ID:** {SESSION_ID}\n"
    transcript += f"**Harness ID:** {HARNESS_ID}\n"
    transcript += f"**Truth Mode:** truth_safe_unverified\n\n"

    for i, prompt in enumerate(TURN_PROMPTS):
        turn_num = i + 1
        transcript += f"### Turn {turn_num}: Control/Judge\n{prompt}\n\n"
        print(f"Running Turn {turn_num}...")
        
        messages.append({"role": "user", "content": prompt})
        response = call_gemma(messages)
        messages.append({"role": "assistant", "content": response})
        
        transcript += f"### Turn {turn_num}: Player ({PLAYER_ID})\n{response}\n\n"
        
        # Intermediate save
        with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(transcript)

    print(f"Transcript complete: {TRANSCRIPT_PATH}")

if __name__ == "__main__":
    run_transcript()
