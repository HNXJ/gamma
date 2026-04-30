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
from gamma_runtime.tool_harness import ToolRouter, ContextHydrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CouncilApp")

class CouncilOrchestrator:
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, 
                 blackboard: Optional[Blackboard] = None,
                 tool_routers: Optional[Dict[str, ToolRouter]] = None,
                 context_hydrator: Optional[ContextHydrator] = None):
        self.scheduler = scheduler
        self.registry = registry
        self.blackboard = blackboard
        self.tool_routers = tool_routers or {}
        self.context_hydrator = context_hydrator

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
            
            for agent in agents:
                logger.info(f"Agent {agent.agent_id} turn starting...")
                
                # 1. Build Initial Request
                req = self._build_request(agent)
                
                # 2. Check for Tool Harness Integration
                router = self.tool_routers.get(agent.agent_id)
                if router:
                    # Execute Tool Loop
                    result_text = await self._run_tool_loop(agent, req, router)
                else:
                    # Standard Inference
                    result = await self.scheduler.schedule(agent.model_key, req)
                    result_text = result.text
                
                await self.blackboard.add_entry(agent.agent_id, result_text)
                logger.info(f"[{agent_id}] Entry committed to blackboard.")
                
        return self.blackboard

    async def _run_tool_loop(self, agent: AgentSpec, initial_req: InferenceRequest, router: ToolRouter) -> str:
        """
        Implements the OpenAI-compatible tool loop.
        """
        messages = list(initial_req.messages) # Shallow copy is enough for top level
        tools = router.get_tool_schema()
        
        # Turn 1: Initial Prompt with Tools
        req = InferenceRequest(
            session_id=initial_req.session_id,
            agent_id=initial_req.agent_id,
            model_key=initial_req.model_key,
            messages=messages,
            generation={**initial_req.generation, "tools": tools, "tool_choice": "auto"},
            adapter_stack=initial_req.adapter_stack
        )
        
        res = await self.scheduler.schedule(agent.model_key, req)
        
        # Parse for tool calls
        assistant_msg = res.raw["choices"][0]["message"]
        messages.append(assistant_msg)
        
        if assistant_msg.get("tool_calls"):
            # Turn 2: Execute and provide results
            tool_results = await router.handle_tool_calls(messages, assistant_msg["tool_calls"])
            messages.extend(tool_results)
            
            # Final Inference
            final_req = InferenceRequest(
                session_id=initial_req.session_id,
                agent_id=initial_req.agent_id,
                model_key=initial_req.model_key,
                messages=messages,
                generation=initial_req.generation,
                adapter_stack=initial_req.adapter_stack
            )
            final_res = await self.scheduler.schedule(agent.model_key, final_req)
            return final_res.text
            
        return res.text

    def _build_request(self, agent: AgentSpec) -> InferenceRequest:
        history = self.blackboard.get_history()
        context = "\n".join([f"{e.sender}: {e.content}" for e in history])
        task = f"Provide your specialized analysis based on your role for the topic: {self.blackboard.topic}"
        
        # Layering: Use ContextHydrator if available
        if self.context_hydrator:
            system_prompt = self.context_hydrator.hydrate(
                agent_role=agent.role,
                memory="TBD (Long-term memory integration)",
                task=task,
                active_skills=agent.routing_tags # Use tags as skill hints
            )
        else:
            system_prompt = agent.system_prompt

        prompt = (
            f"Topic: {self.blackboard.topic}\n"
            f"Round: {self.blackboard.round}\n\n"
            f"History:\n{context}\n\n"
        )
        
        return InferenceRequest(
            session_id=f"council-{self.blackboard.topic[:10]}",
            agent_id=agent.agent_id,
            model_key=agent.model_key,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            generation=agent.generation,
            adapter_stack=agent.adapter_stack
        )

async def main():
    from gamma_runtime.orchestrator import UnifiedOrchestrator
    from gamma_runtime.hub_api import HubAPIServer
    from gamma_runtime.config import get_lms_url, HUB_PORT
    root = os.getcwd()
    config_path = os.path.join(root, "context", "configs")
    registry = RuntimeRegistry(config_path)
    scheduler = InferenceScheduler()
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    council = CouncilOrchestrator(scheduler, registry)
    await council.initialize_pools(["gemma4-parallel", "gemma-9b-schiz"], lambda spec: LMStudioBackend(get_lms_url()))
    api = HubAPIServer(orchestrator, port=HUB_PORT)
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
