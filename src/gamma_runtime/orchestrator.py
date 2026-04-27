import asyncio
import logging
from typing import Dict, Any, Optional, List
from .types import AgentId, InferenceRequest
from .scheduler import InferenceScheduler
from .blackboard import Blackboard
from .registry import RuntimeRegistry
from .consolidation import ConsolidationManager
from apps.council_app import CouncilOrchestrator
from sde_engine.solver import SDESolver

logger = logging.getLogger("UnifiedOrchestrator")

class UnifiedOrchestrator:
    """
    The High-Level Controller for the Gamma Scientific Stack.
    Bridges Linguistic (Council) and Biophysical (SDE) reasoning.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry):
        self.scheduler = scheduler
        self.registry = registry
        self.consolidation = ConsolidationManager()
        self._active_sessions: Dict[str, Blackboard] = {}

    async def launch_run(self, run_type: str, topic: str, **kwargs) -> str:
        """
        Launches a scientific session.
        run_type: 'council', 'sde', or 'synthesis'
        """
        session_id = f"session-{run_type}-{asyncio.get_event_loop().time()}"
        blackboard = Blackboard(topic)
        self._active_sessions[session_id] = blackboard
        
        # Start the run in the background to avoid blocking the API
        asyncio.create_task(self._execute_run(run_type, blackboard, **kwargs))
        
        return session_id

    async def _execute_run(self, run_type: str, blackboard: Blackboard, **kwargs):
        try:
            if run_type == "council":
                orchestrator = CouncilOrchestrator(self.scheduler, self.registry, blackboard=blackboard)
                await orchestrator.run_deliberation(
                    team_id=kwargs.get("team_id", "sde_debate_team"),
                    topic=blackboard.topic,
                    rounds=kwargs.get("rounds", 2)
                )
            elif run_type == "sde":
                solver = SDESolver(self.scheduler, blackboard=blackboard)
                # Load proponent/adversary from registry
                proponent = self.registry.load_agent(kwargs.get("proponent_id", "excitatory_specialist"))
                adversary = self.registry.load_agent(kwargs.get("adversary_id", "inhibitory_specialist"))
                await solver.run_optimization_cycle(proponent, adversary)
            elif run_type == "synthesis":
                # A combined pass: Council sets constraints, SDE optimizes
                logger.info("Executing Full Synthesis Run (Council -> SDE)")
                # ... implementation details ...
                pass
            
            logger.info(f"Session {run_type} completed successfully.")
            
            # AUTOMATED CONSOLIDATION: Trigger FedLoRA if consensus is reached
            if kwargs.get("auto_consolidate", True):
                payload_path = self.consolidation.extract_validated_traces(blackboard, blackboard.topic[:10])
                if payload_path:
                    # In a real run, we'd use the model_key from the agents
                    await self.consolidation.trigger_training(payload_path, "gemma-9b-schiz")
                    
        except Exception as e:
            logger.error(f"Session failed: {e}")
            await blackboard.add_entry(sender="SYSTEM", content=f"ERROR: {str(e)}")

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        blackboard = self._active_sessions.get(session_id)
        if not blackboard: return None
        
        return {
            "session_id": session_id,
            "topic": blackboard.topic,
            "round": blackboard.round,
            "entries": [
                {
                    "sender": e.sender,
                    "content": e.content,
                    "timestamp": e.timestamp.isoformat(),
                    "metadata": e.metadata
                } for e in blackboard.entries
            ]
        }
