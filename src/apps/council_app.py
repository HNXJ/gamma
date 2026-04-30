import asyncio
import logging
import os
from typing import List, Dict, Optional
from gamma_runtime.types import AgentSpec, InferenceRequest
from gamma_runtime.scheduler import InferenceScheduler, ResourceBudget
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.model_pool import SharedModelPool
from gamma_runtime.backend_lmstudio import LMStudioBackend

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CouncilApp")

class CouncilOrchestrator:
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, blackboard: Optional[Blackboard] = None):
        self.scheduler = scheduler
        self.registry = registry
        self.blackboard = blackboard

    async def initialize_pools(self, model_keys: List[str], backend_factory):
        for key in model_keys:
            try:
                spec = self.registry.load_model(key)
                backend = backend_factory(spec)
                pool = SharedModelPool(spec, backend)
                await self.scheduler.register_pool(pool)
                logger.info(f"Registered model pool: {key}")
            except Exception as e:
                logger.error(f"Failed to initialize pool {key}: {e}")

    async def run_deliberation(self, team_id: str, topic: str, rounds: int = 2):
        if not self.blackboard:
            self.blackboard = Blackboard(topic)
        team_config = self.registry.load_team(team_id)
        agents = [self.registry.load_agent(aid) for aid in team_config["agents"]]
        logger.info(f"🚀 INITIATING DELIBERATION: '{topic}'")
        for r in range(rounds):
            self.blackboard.round = r + 1
            requests = []
            for agent in agents:
                req = self._build_request(agent)
                requests.append((agent.model_key, req))
            results = await self.scheduler.batch_run(requests)
            for i, result in enumerate(results):
                agent_id = agents[i].agent_id
                await self.blackboard.add_entry(agent_id, result.text)
                logger.info(f"[{agent_id}] Entry committed to blackboard.")
        return self.blackboard

    def _build_request(self, agent: AgentSpec) -> InferenceRequest:
        history = self.blackboard.get_history()
        context = "\n".join([f"{e.sender}: {e.content}" for e in history])
        prompt = (
            f"Topic of Discussion: {self.blackboard.topic}\n"
            f"Round: {self.blackboard.round}\n\n"
            f"Deliberation History:\n{context}\n\n"
            f"Your Task: Provide your specialized analysis based on your role."
        )
        return InferenceRequest(
            session_id=f"council-{self.blackboard.topic[:10]}",
            agent_id=agent.agent_id,
            model_key=agent.model_key,
            messages=[{"role": "system", "content": agent.system_prompt}, {"role": "user", "content": prompt}],
            generation=agent.generation,
            adapter_stack=agent.adapter_stack
        )

async def main():
    from gamma_runtime.orchestrator import UnifiedOrchestrator
    from gamma_runtime.hub_api import HubAPIServer
    root = os.getcwd()
    config_path = os.path.join(root, "context", "configs")
    registry = RuntimeRegistry(config_path)
    scheduler = InferenceScheduler()
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    council = CouncilOrchestrator(scheduler, registry)
    await council.initialize_pools(["gemma4-parallel", "gemma-9b-schiz"], lambda spec: LMStudioBackend("http://127.0.0.1:1234"))
    api = HubAPIServer(orchestrator, port=8001)
    api.start()
    orchestrator.start_heartbeat_monitor(team_id="v1_gamma_sde_team", topic="SDE Biophysical Property Extraction")
    logger.info("🏟️  GAMMA ARENA BOOTED SUCCESSFULLY.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
