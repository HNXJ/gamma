import asyncio
import logging
import json
import os
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
from gamma_runtime.structs import AgentSpec, InferenceRequest, InferenceResult, ToolLoopResult
from gamma_runtime.scheduler import InferenceScheduler, ResourceBudget
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.bridge.v1_gamma_bridge import V1GammaBridge
from gamma_runtime.bridge.path_topology import GameLogTopology
from gamma_runtime.tool_loop import execute_tool_loop

logger = logging.getLogger('CouncilApp')

class CouncilOrchestrator:
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, heartbeat, blackboard: Optional[Blackboard] = None, game_id: str = 'game001'):
        self.scheduler = scheduler
        self.registry = registry
        self.heartbeat = heartbeat
        self.blackboard = blackboard or Blackboard("Council Deliberation")
        self.game_id = game_id
        self.root = Path('/Users/HN/MLLM/gamma')
        self.topology = GameLogTopology(self.root, game_id)
        self.bridge = V1GammaBridge(self.blackboard, enabled=True, game_id=game_id)
        
        self.logger = logging.getLogger('Orchestrator')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(self.topology.get_log_path('orchestrator'))
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)

    def _get_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    async def run_deliberation(self, topic: str, team_id: str, rounds: int = 1, audit_mode: bool = True):
        self.logger.info(f"🚀 INITIATING ROLE-ISOLATION AUDIT: '{topic}' [Game: {self.game_id}]")
        agent_ids = ["v1_gamma_proponent", "v1_gamma_adversary", "v1_gamma_judge"]
        
        nonces = {
            "v1_gamma_proponent": "ALPHA-77",
            "v1_gamma_adversary": "BETA-91",
            "v1_gamma_judge": "GAMMA-23"
        }

        for r in range(1, rounds + 1):
            self.logger.info(f"--- Round {r} ---")
            for agent_id in agent_ids:
                agent = self.registry.get_agent(agent_id)
                if not agent: continue
                
                agent_logger = logging.getLogger(f'Agent_{agent_id}')
                agent_logger.setLevel(logging.INFO)
                if not agent_logger.handlers:
                    afh = logging.FileHandler(self.topology.get_log_path(f'agent-{agent_id}'))
                    afh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
                    agent_logger.addHandler(afh)

                nonce = nonces.get(agent_id, "DEFAULT-0")
                
                if "proponent" in agent_id:
                    role_goal = "PROPOSE stable parameters. CITE YOUR NONCE."
                elif "adversary" in agent_id:
                    role_goal = "CRITIQUE proposals. CITE YOUR NONCE."
                else:
                    role_goal = "AUDIT system state. CITE YOUR NONCE."

                sys_prompt = agent.system_prompt + f"\n\nYOUR ROLE GOAL: {role_goal}\nNONCE: {nonce}\nMANDATE: You MUST use run_python for simulation. Cite your NONCE in every response."
                user_prompt = f"Topic: {topic}. Previous deliberation: {self.blackboard.get_recent_summary()}. Current Round: {r}."

                self.logger.info(f"AUDIT [{agent_id}] - SysHash: {self._get_hash(sys_prompt)} | UserHash: {self._get_hash(user_prompt)}")
                self.logger.info(f"AUDIT [{agent_id}] - Nonce: {nonce} | Temp: {agent.generation.get('temperature', 0.4)}")

                messages = [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                # Run tool loop
                result: ToolLoopResult = await execute_tool_loop(
                    self.scheduler, agent, messages, self.game_id, agent_logger
                )
                
                # Update Heartbeat State
                self.heartbeat.update_agent(agent_id, {
                    "input_chars": result.input_chars,
                    "output_chars": result.output_chars,
                    "usage_tokens": result.usage_tokens,
                    "last_tool_name": result.last_tool_name,
                    "is_idle_review": False
                })

                self.logger.info(f"AUDIT [{agent_id}] - Raw Output Length: {len(result.final_text)}")
                if nonce not in result.final_text:
                    self.logger.error(f"AUDIT [{agent_id}] - NONCE MISSING IN OUTPUT!")
                else:
                    self.logger.info(f"AUDIT [{agent_id}] - NONCE VERIFIED.")

                await self.blackboard.add_entry(
                    sender=agent_id,
                    content=result.final_text,
                    metadata={
                        "round": r, 
                        "mode": "audit", 
                        "nonce": nonce,
                        "metrics": {
                            "input_chars": result.input_chars,
                            "output_chars": result.output_chars,
                            "usage_tokens": result.usage_tokens
                        }
                    }
                )
                
                if "proponent" in agent_id or "adversary" in agent_id:
                    asyncio.create_task(self.bridge.process_proposal(agent_id, result.final_text, r))
                    
        return "success"
