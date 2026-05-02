import asyncio
import os
import sys
import logging

# Anchor to project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("T00Proof")

async def run_proof():
    from gamma_runtime.scheduler import InferenceScheduler
    from gamma_runtime.registry import RuntimeRegistry
    from gamma_runtime.orchestrator import UnifiedOrchestrator
    
    # 1. Initialize Registry and Scheduler
    registry = RuntimeRegistry(os.path.join(ROOT, "context/configs"))
    scheduler = InferenceScheduler()
    
    # 2. Initialize Orchestrator
    orchestrator = UnifiedOrchestrator(
        scheduler, 
        registry
    )
    
    # 3. Launch T00 Tutorial
    logger.info("🚀 Launching T00 Tutorial Proof Run...")
    session_id = await orchestrator.launch_run(
        run_type="tutorial",
        topic="T00 Single Neuron HH Smoke Test",
        tutorial_id="T00_single_neuron_hh"
    )
    
    logger.info(f"Session {session_id} launched. Waiting for completion...")
    
    # Poll for completion (simple wait for now as it's a proof script)
    # In a real run, we'd check blackboard or session state
    await asyncio.sleep(10)
    
    state = orchestrator.get_session_state(session_id)
    if state:
        for entry in state["entries"]:
            logger.info(f"[{entry['sender']}] {entry['content']}")
            if entry["metadata"].get("type") == "tutorial_result":
                run_id = entry["metadata"]["run_id"]
                artifact_dir = os.path.join(ROOT, "data/tutorials/artifacts/T00_single_neuron_hh", run_id)
                logger.info(f"✅ Tutorial Result Found. Artifacts at: {artifact_dir}")
                
                # Check for required artifacts
                required = ["summary_metrics.json", "evaluation_decision.json", "v_trace.npy", "run_manifest.json"]
                for f in required:
                    fpath = os.path.join(artifact_dir, f)
                    if os.path.exists(fpath):
                        logger.info(f"  - {f} exists")
                    else:
                        logger.error(f"  - {f} MISSING")

if __name__ == "__main__":
    asyncio.run(run_proof())
