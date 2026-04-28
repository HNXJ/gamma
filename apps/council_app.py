import asyncio
import logging
from typing import List, Dict, Optional
from gamma_runtime.types import AgentSpec, InferenceRequest
from gamma_runtime.scheduler import InferenceScheduler, ResourceBudget
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.trace_schema import TraceEntry, ConsensusLevel, TraceMode

logger = logging.getLogger('CouncilApp')

def resolve_team_agent_ids(team_config) -> list[str]:
    if isinstance(team_config, dict):
        return team_config.get("agent_ids") or team_config.get("agents") or []
    return getattr(team_config, "agent_ids", None) or getattr(team_config, "agents", None) or []

class CouncilOrchestrator:
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, blackboard: Optional[Blackboard] = None):
        self.scheduler = scheduler
        self.registry = registry
        self.blackboard = blackboard or Blackboard("Council Deliberation")

    async def run_deliberation(self, topic: str, team_id: str, rounds: int = 3):
        logger.info(f"🚀 INITIATING DELIBERATION: '{topic}'")
        team_config = self.registry.get_team(team_id)
        agent_ids = resolve_team_agent_ids(team_config)
        if not agent_ids:
            raise ValueError(f"Team {team_id} has no agents/agent_ids configured")
        
        logger.info(f"Team: {team_id} ({len(agent_ids)} agents)")
        
        for r in range(1, rounds + 1):
            logger.info(f"--- Round {r} ---")
            tasks = []
            for agent_id in agent_ids:
                agent = self.registry.get_agent(agent_id)
                request = InferenceRequest(
                    session_id="session",
                    agent_id=agent_id,
                    model_key=agent.model_key,
                    messages=[
                        {"role": "system", "content": agent.system_prompt},
                        {"role": "user", "content": f"Context: {topic}. Previous deliberation: {self.blackboard.get_recent_summary()}"}
                    ],
                    generation=agent.generation,
                    adapter_stack=[]
                )
                # Corrected: Passing model_key and request
                tasks.append(self.scheduler.schedule(agent.model_key, request))
            
            results = await asyncio.gather(*tasks)
            for i, res in enumerate(results):
                await self.blackboard.add_entry(
                    sender=agent_ids[i],
                    content=res.text,
                    metadata={"round": r, "mode": "council"}
                )
        return "success"
