import argparse
import asyncio
import logging
import sys
import os
from pathlib import Path

ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.orchestrator import UnifiedOrchestrator
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.hub_api import HubAPIServer

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--run_type", default="council", choices=["council", "sde", "synthesis"])
    p.add_argument("--team", default="v1_gamma_sde_team")
    p.add_argument("--rounds", type=int, default=12)
    p.add_argument("--topic", default="V1 gamma SDE optimization")
    p.add_argument("--dashboard_port", type=int, default=3012)
    p.add_argument("--model_key", default="gemma-4-e4b-it-mxfp8")
    p.add_argument("--lmstudio_url", default="http://127.0.0.1:1234")
    p.add_argument("--game_id", default="game001")
    p.add_argument("--start_server", action="store_true")
    p.add_argument("--auto_consolidate", action="store_true")
    return p.parse_args()

async def main():
    args = parse_args()

    # Base logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("OvernightConsensus")

    registry = RuntimeRegistry(str(ROOT / "configs"))
    model_spec = registry.load_model(args.model_key)

    scheduler = InferenceScheduler()
    backend = LMStudioBackend(
        base_url=args.lmstudio_url,
        preload_via_cli=True,
        start_server=args.start_server,
    )
    pool = SharedModelPool(model_spec, backend)
    await scheduler.register_pool(pool)

    orchestrator = UnifiedOrchestrator(scheduler, registry)
    
    # Start Hub API / Dashboard Server
    api_server = HubAPIServer(orchestrator, port=args.dashboard_port)
    api_server.start()

    logger.info(f"=== GAMMA OVERNIGHT CONSENSUS INITIATED [{args.game_id}] ===")

    session_id = await orchestrator.launch_run(
        run_type=args.run_type,
        topic=args.topic,
        team_id=args.team,
        rounds=args.rounds,
        game_id=args.game_id,
        auto_consolidate=args.auto_consolidate,
    )

    logger.info("Session %s active. Monitor at http://localhost:%d", session_id, args.dashboard_port)

    try:
        while True:
            await asyncio.sleep(600)
    finally:
        await backend.handler.close()

if __name__ == "__main__":
    asyncio.run(main())
