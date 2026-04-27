import asyncio
import logging
from typing import List, Dict
from gamma_runtime.types import AgentSpec, InferenceRequest
from gamma_runtime.scheduler import InferenceScheduler, ResourceBudget
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.model_pool import SharedModelPool

# Configure logging for scientific transparency
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CouncilApp")

class CouncilOrchestrator:
    """
    Sovereign Orchestrator for the Gemma Council.
    Implements the Blackboard pattern and managed execution via InferenceScheduler.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, blackboard: Optional[Blackboard] = None):
        self.scheduler = scheduler
        self.registry = registry
        self.blackboard = blackboard

    async def initialize_pools(self, model_keys: List[str], backend_factory):
        """Ensures all required model pools are registered in the scheduler."""
        for key in model_keys:
            spec = self.registry.load_model(key)
            backend = backend_factory(spec)
            pool = SharedModelPool(spec, backend)
            await self.scheduler.register_pool(pool)
            logger.info(f"Registered model pool: {key}")

    async def run_deliberation(self, team_id: str, topic: str, rounds: int = 2):
        """
        Executes the multi-agent deliberation loop.
        Routes all execution through the scheduler to protect VRAM.
        """
        if not self.blackboard:
            self.blackboard = Blackboard(topic)
        
        team_config = self.registry.load_team(team_id)
        agents = [self.registry.load_agent(aid) for aid in team_config["agents"]]
        
        logger.info(f"🚀 INITIATING DELIBERATION: '{topic}'")
        logger.info(f"Team: {team_id} ({len(agents)} agents)")

        for r in range(rounds):
            self.blackboard.round = r + 1
            logger.info(f"--- Round {self.blackboard.round} ---")
            
            # Managed Parallel Execution via Scheduler
            # We construct a list of (model_key, request) tuples for the scheduler
            requests = []
            for agent in agents:
                req = self._build_request(agent)
                requests.append((agent.model_key, req))
            
            # Execute batch through the scheduler's budget check
            results = await self.scheduler.batch_run(requests)
            
            # Update blackboard with results
            for i, result in enumerate(results):
                agent_id = agents[i].agent_id
                await self.blackboard.add_entry(agent_id, result.text)
                logger.info(f"[{agent_id}] Entry committed to blackboard.")

        logger.info(f"✅ DELIBERATION COMPLETE. Entries: {len(self.blackboard.entries)}")
        return self.blackboard

    def _build_request(self, agent: AgentSpec) -> InferenceRequest:
        """Constructs an InferenceRequest using the current blackboard state."""
        history = self.blackboard.get_history()
        
        # Simple context synthesis: Provide previous entries to the agent
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
            messages=[
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": prompt}
            ],
            generation=agent.generation,
            adapter_stack=agent.adapter_stack
        )

async def main():
    """Entry point for manual council execution."""
    # This would normally be called by a higher-level script or the Hub API
    pass

if __name__ == "__main__":
    asyncio.run(main())
