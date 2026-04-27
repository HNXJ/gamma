import sys
import os
import asyncio
import logging

# Anchor to project root for module imports
ROOT = "/Users/hamednejat/workspace/computational/gamma"
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from src.gamma_runtime.scheduler import InferenceScheduler
from src.gamma_runtime.backend_lmstudio import LMStudioBackend
from src.gamma_runtime.registry import RuntimeRegistry
from src.gamma_runtime.orchestrator import UnifiedOrchestrator
from src.gamma_runtime.types import ModelSpec

# 1. Setup Robust Logging
log_file = os.path.join(ROOT, "data/overnight_run.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OvernightConsensus")

async def main():
    logger.info("=== GAMMA OVERNIGHT CONSENSUS INITIATED ===")
    logger.info(f"Targeting: M3 Max (Shared Context Pool, n=4)")
    
    # 2. Initialize Infrastructure
    registry = RuntimeRegistry(os.path.join(ROOT, "configs"))
    backend = LMStudioBackend()
    
    # Define Model Spec for the E4B (Gemma 4B) model
    model_spec = ModelSpec(
        key="gemma-4-e4b-it-mxfp8",
        provider="lmstudio",
        context_length=4096,
        max_parallel_slots=4
    )
    
    # Correct Scheduler/Pool Initialization
    from src.gamma_runtime.model_pool import SharedModelPool
    from src.gamma_runtime.scheduler import InferenceScheduler
    
    scheduler = InferenceScheduler()
    pool = SharedModelPool(model_spec, backend)
    await scheduler.register_pool(pool)
    
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    
    # 3. Define the Overnight Scientific Objective
    topic = "Hierarchical Predictive Coding (HPC) Optimization: Mapping inhibitory landscapes across 13 laminar epochs to maximize Epistemic Gain (x) and Bio-Plausibility (z)."
    
    logger.info(f"Launching Task: {topic}")
    
    # 4. Execute the Run
    # Launching in 'council' mode with the 4-agent team
    session_id = await orchestrator.launch_run(
        run_type="council",
        topic=topic,
        team_id="e4b_overnight_team",
        rounds=50, # Sufficient for overnight deliberation
        auto_consolidate=True
    )
    
    logger.info(f"Session {session_id} is now active in the Shared Context Pool.")
    logger.info("Agents: Macro-Strategist, Meso-Architect, Micro-Validator, Adversarial-Critic.")
    
    # 5. Persistent Monitoring Loop
    # This keeps the main process alive while the background task executes
    try:
        while True:
            state = orchestrator.get_session_state(session_id)
            if state:
                num_entries = len(state["entries"])
                logger.info(f"Heartbeat: {num_entries} entries in Blackboard for {session_id}")
            await asyncio.sleep(600) # Heartbeat every 10 minutes
    except Exception as e:
        logger.error(f"Monitoring loop encountered an error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process received SIGINT. Shutting down gracefully.")
