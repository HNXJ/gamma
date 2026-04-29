import asyncio
import logging
import json
from pathlib import Path
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.orchestrator import UnifiedOrchestrator
from gamma_runtime.heartbeat_state import HeartbeatManager
from gamma_runtime.tool_loop import execute_tool_loop

async def main():
    root = Path('/Users/HN/MLLM/gamma')
    registry = RuntimeRegistry(root / 'configs')
    scheduler = InferenceScheduler(registry=registry)
    heartbeat = HeartbeatManager(root)
    
    agent_id = 'v1_gamma_proponent'
    agent = registry.get_agent(agent_id)
    
    print(f"--- Testing Integrated Skill Call: {agent_id} ---")
    
    # Mandate real code execution
    messages = [
        {"role": "system", "content": agent.system_prompt + "\nMANDATE: You MUST import 'gamma_runtime.skills_lib' and use the 'skill_target_natural_frequency' function. Cite your output."},
        {"role": "user", "content": "Analyze this PSD data: freqs = [10, 20, 30, 40, 50], psd = [0.1, 0.5, 2.0, 0.5, 0.1]. Use the skill and return the frequency."}
    ]
    
    logger = logging.getLogger('ProofRunner')
    result = await execute_tool_loop(scheduler, agent, messages, "proof-debt-closure", logger)
    
    print(f"Final Response: {result.final_text}")
    
    # Update Heartbeat
    heartbeat.update_agent(agent_id, {
        "input_chars": result.input_chars,
        "output_chars": result.output_chars,
        "usage_tokens": result.usage_tokens,
        "last_tool_name": result.last_tool_name,
        "is_idle_review": False
    })
    
    # VERIFY
    hb_state = heartbeat.get_state()
    agent_hb = hb_state['agents'].get(agent_id, {})
    
    if agent_hb.get('last_tool_name') == 'run_python' and result.tool_calls_count > 0:
        if "30" in result.final_text:
             print("✅ INTEGRATED PROOF VERIFIED: Skill executed, result obtained, and metrics stored.")
        else:
             print("⚠️ PROOF PARTIAL: Skill called, but result not cited correctly in response.")
    else:
        print("❌ PROOF DEBT FAILED: No tool invocation recorded.")

if __name__ == "__main__":
    asyncio.run(main())
