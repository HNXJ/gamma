import asyncio
import json
import logging
import os
import time
from typing import Optional, Dict, Any
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.runtime_types import MissionContext, AgentSpec, InferenceRequest
from apps.council_app import CouncilOrchestrator
from gamma_runtime.tool_harness import ToolRouter, ContextHydrator
from gamma_runtime.mechanistic_protocol import MECHANISTIC_PROTOCOL

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
                logger.info(f"Agent {agent.agent_id} Contribution: {result_text}")
                
                if agent.agent_id == "G01":
                    self._emit_proposal(self.blackboard.round, result_text)

        logger.info("✅ V1 GAMMA SDE DELIBERATION COMPLETE.")
        return self.blackboard

    def _emit_proposal(self, epoch: int, content: str):
        try:
            # 1. Extract JSON block (STRICT)
            if "```json" not in content:
                logger.warning(f"❌ PROPOSAL REJECTED: Missing required JSON block.")
                return
            
            json_str = content.split("```json")[1].split("```")[0].strip()
            
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
        except json.JSONDecodeError as e:
            debug_path = "/Users/hamednejat/workspace/computational/gamma/local/run/debug_proposal.json"
            with open(debug_path, "w") as f:
                f.write(json_str)
            logger.error(f"💥 Proposal parse error saved to {debug_path}: {e}")
            return
        except Exception as e:
            logger.error(f"💥 Failed to parse/emit proposal JSON: {e}")

    def _build_request(self, agent: AgentSpec) -> InferenceRequest:
        """
        Overrides CouncilOrchestrator to inject Mechanistic Protocol if in exploratory/tutorial mode.
        """
        history = self.blackboard.get_history()
        context = "\n".join([f"{e.sender}: {e.content}" for e in history])
        task = f"Provide your specialized mechanistic analysis for the topic: {self.blackboard.topic}"
        
        # Determine if we should enforce the mechanistic contract
        protocol = None
        if self.mission_context.mission_kind in ("tutorial", "exploratory"):
            protocol = MECHANISTIC_PROTOCOL

        if self.context_hydrator:
            system_prompt = self.context_hydrator.hydrate(
                agent_role=agent.role,
                memory="TBD (Long-term memory integration)",
                task=task,
                active_skills=agent.routing_tags,
                protocol=protocol
            )
        else:
            system_prompt = f"{agent.system_prompt}\n\n{protocol if protocol else ''}"

        prompt = (
            f"Topic: {self.blackboard.topic}\n"
            f"Round: {self.blackboard.round}\n\n"
            f"History:\n{context}\n\n"
        )
        
        return InferenceRequest(
            session_id=f"v1-sde-{self.blackboard.topic[:10]}",
            agent_id=agent.agent_id,
            model_key=agent.model_key,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            generation=agent.generation,
            adapter_stack=agent.adapter_stack
        )
