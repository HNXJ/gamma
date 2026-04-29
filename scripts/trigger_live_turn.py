import asyncio
import sys
import os
from pathlib import Path
import json
import time

# Fix paths
root = Path('/Users/HN/MLLM/gamma')
sys.path.append(str(root / 'src'))
sys.path.append(str(root)) # for apps

from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.orchestrator import UnifiedOrchestrator
from gamma_runtime.blackboard import Blackboard

async def main():
    registry = RuntimeRegistry(root / 'configs')
    scheduler = InferenceScheduler(registry)
    orch = UnifiedOrchestrator(scheduler, registry)
    
    game_id = "game001"
    topic = "Grounded Bootstrap Mission: Stabilize 10-neuron Circuit"
    bb = Blackboard(topic)
    
    # Clear seen for the new announcement to ensure it is read
    for agent_id in ["v1_gamma_proponent", "v1_gamma_adversary", "v1_gamma_judge", "v1_gamma_tester"]:
        seen_path = os.path.join(root, 'local', game_id, f'mail/agents/{agent_id}/seen/ann_bootstrap_update_002.json')
        if os.path.exists(seen_path):
            os.remove(seen_path)
    
    from apps.council_app import CouncilOrchestrator
    from gamma_runtime.heartbeat_state import HeartbeatManager
    
    hb = HeartbeatManager(root)
    corch = CouncilOrchestrator(scheduler, registry, hb, blackboard=bb, game_id=game_id)
    
    print(f"Triggering live turn for {game_id} with new grounded announcement...")
    await corch.run_deliberation(topic=topic, team_id="v1_gamma_sde_team", rounds=1)
    
    entries = bb.get_history()
    print(f"Total entries: {len(entries)}")
    for e in entries:
        if e.sender == 'bridge': continue
        print(f"--- {e.sender} ---")
        print(e.content)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
