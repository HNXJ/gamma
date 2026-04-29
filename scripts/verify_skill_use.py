import asyncio
import os
import sys
from pathlib import Path

# Set up path to import from src
sys.path.append('/Users/HN/MLLM/gamma/src')
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.tool_loop import execute_tool_loop

async def verify_skill_use():
    registry = RuntimeRegistry(Path('/Users/HN/MLLM/gamma/configs'))
    scheduler = InferenceScheduler() # Mock scheduler for direct call
    
    agent_id = 'v1_gamma_proponent'
    agent = registry.get_agent(agent_id)
    
    # Force a scenario where a skill is needed
    messages = [
        {"role": "system", "content": agent.system_prompt + "\n\nCRITICAL: Use the 'skill_target_natural_frequency' from 'skills_lib.py' to analyze the provided PSD. Do not write your own peak detection logic."},
        {"role": "user", "content": "I have a PSD array from a 30Hz target simulation. freqs = [10, 20, 30, 40, 50], psd = [0.1, 0.5, 2.5, 0.4, 0.1]. Use the registered skill to verify the peak."}
    ]
    
    print(f"--- Launching Skill Use Verification for {agent_id} ---")
    response = await execute_tool_loop(
        scheduler, agent, messages, "skill-verify-run", None
    )
    print("\n--- FINAL RESPONSE ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(verify_skill_use())
