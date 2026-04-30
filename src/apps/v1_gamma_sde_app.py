import asyncio
import json
import logging
import os
import time
from typing import Optional, Dict, Any
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.types import MissionContext
from apps.council_app import CouncilOrchestrator
from gamma_runtime.tool_harness import ToolRouter, ContextHydrator

logger = logging.getLogger("V1GammaSDEApp")

class V1GammaSDEOrchestrator(CouncilOrchestrator):
    """
    Thin wrapper around the CouncilOrchestrator specifically designed for the V1 Gamma SDE Game.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, 
                 mission_context: MissionContext, 
                 blackboard: Optional[Blackboard] = None,
                 tool_routers: Optional[Dict[str, ToolRouter]] = None,
                 context_hydrator: Optional[ContextHydrator] = None):
        super().__init__(scheduler, registry, blackboard, tool_routers, context_hydrator)
        self.mission_context = mission_context
        self.proposals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sde_proposals")
        os.makedirs(self.proposals_dir, exist_ok=True)

    async def run_deliberation(self, team_id: str, topic: str, rounds: int = 2):
        if not self.blackboard:
            self.blackboard = Blackboard(topic)
        
        team_config = self.registry.load_team(team_id)
        agents = [self.registry.load_agent(aid) for aid in team_config["agents"]]
        
        logger.info(f"🚀 INITIATING V1 GAMMA SDE DELIBERATION: '{topic}'")

        for r in range(rounds):
            self.blackboard.round = r + 1
            logger.info(f"--- SDE Epoch {self.blackboard.round} ---")
            
            for agent in agents:
                logger.info(f"Agent {agent.agent_id} turn starting...")
                req = self._build_request(agent)
                
                router = self.tool_routers.get(agent.agent_id)
                if router:
                    result_text = await self._run_tool_loop(agent, req, router)
                else:
                    result = await self.scheduler.schedule(agent.model_key, req)
                    result_text = result.text
                
                await self.blackboard.add_entry(agent.agent_id, result_text)
                
                if agent.agent_id == "v1_gamma_proponent":
                    self._emit_proposal(self.blackboard.round, result_text)

        logger.info("✅ V1 GAMMA SDE DELIBERATION COMPLETE.")
        return self.blackboard

    def _emit_proposal(self, epoch: int, content: str):
        try:
            # 1. Extract JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                else:
                    return

            # 2. Parse JSON
            proposal = json.loads(json_str)
            
            # 3. Schema & Mission Alignment Validation
            rejection_reason = None
            meta = proposal.get("meta")
            
            if not meta or not isinstance(meta, dict):
                rejection_reason = "Missing or malformed 'meta' block."
            elif "neuron_count" not in meta:
                rejection_reason = "Missing 'meta.neuron_count' field."
            elif meta["neuron_count"] != self.mission_context.target_neuron_count:
                rejection_reason = f"Mission Mismatch: Proposal N={meta['neuron_count']} != Target N={self.mission_context.target_neuron_count}"

            if rejection_reason:
                logger.warning(f"❌ PROPOSAL REJECTED: {rejection_reason}")
                return

            # 4. Successful Emission
            if "proposal_id" not in proposal:
                proposal["proposal_id"] = f"epoch_{epoch:02d}_candidate_{int(time.time())}"

            filename = os.path.join(self.proposals_dir, f"{proposal['proposal_id']}.json")
            with open(filename, 'w') as f:
                json.dump(proposal, f, indent=2)
            
            logger.info(f"✅ Emitted mission-aligned proposal: {filename}")
        except Exception as e:
            logger.error(f"💥 Failed to parse/emit proposal JSON: {e}")
