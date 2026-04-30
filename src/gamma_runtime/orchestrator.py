import asyncio
import logging
import time
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
    Now includes an aggressive Zero-Idle Heartbeat Monitor.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry):
        self.scheduler = scheduler
        self.registry = registry
        self.consolidation = ConsolidationManager()
        self._active_sessions: Dict[str, Blackboard] = {}
        self._last_activity_time = time.time()
        self._monitor_task: Optional[asyncio.Task] = None
        self._heartbeat_config: Dict[str, Any] = {
            "team_id": "v1_gamma_sde_team",
            "topic": "Autonomous SDE Refinement",
            "active": False
        }

    def start_heartbeat_monitor(self, team_id: str = "v1_gamma_sde_team", topic: str = "Autonomous SDE Refinement"):
        """Activates the aggressive zero-idle-time heartbeat rule."""
        self._heartbeat_config["team_id"] = team_id
        self._heartbeat_config["topic"] = topic
        self._heartbeat_config["active"] = True
        
        if not self._monitor_task or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._heartbeat_loop())
            logger.info(f"💓 Heartbeat Monitor Activated: Team={team_id}, Rule='Not even a second'")

    async def _heartbeat_loop(self):
        """Aggressive loop: ensures the system never stalls."""
        while self._heartbeat_config["active"]:
            now = time.time()
            idle_duration = now - self._last_activity_time
            
            if idle_duration > 1.0:
                logger.warning(f"⚠️ SYSTEM IDLE DETECTED ({idle_duration:.2f}s). Forcing heartbeat turn...")
                try:
                    # Create a default session if none exists, or use the last one
                    session_id = "heartbeat-session"
                    if session_id not in self._active_sessions:
                        self._active_sessions[session_id] = Blackboard(self._heartbeat_config["topic"])
                    
                    blackboard = self._active_sessions[session_id]
                    self._last_activity_time = now # Prevent re-triggering while running
                    
                    # Execute a single round of deliberation
                    orchestrator = CouncilOrchestrator(self.scheduler, self.registry, blackboard=blackboard)
                    await orchestrator.run_deliberation(
                        team_id=self._heartbeat_config["team_id"],
                        topic=blackboard.topic,
                        rounds=1
                    )
                    self._last_activity_time = time.time()
                except Exception as e:
                    logger.error(f"Heartbeat trigger failed: {e}")
                    await asyncio.sleep(5) # Back off on error
            
            await asyncio.sleep(0.5) # High frequency polling

    async def launch_run(self, run_type: str, topic: str, **kwargs) -> str:
        """
        Launches a scientific session.
        run_type: 'council', 'sde', or 'synthesis'
        """
        session_id = f"session-{run_type}-{int(time.time())}"
        blackboard = Blackboard(topic)
        self._active_sessions[session_id] = blackboard
        
        # Start the run in the background
        asyncio.create_task(self._execute_run(run_type, blackboard, **kwargs))
        
        return session_id

    async def _execute_run(self, run_type: str, blackboard: Blackboard, **kwargs):
        try:
            self._last_activity_time = time.time()
            if run_type == "council":
                orchestrator = CouncilOrchestrator(self.scheduler, self.registry, blackboard=blackboard)
                await orchestrator.run_deliberation(
                    team_id=kwargs.get("team_id", "sde_debate_team"),
                    topic=blackboard.topic,
                    rounds=kwargs.get("rounds", 2)
                )
            elif run_type == "sde":
                solver = SDESolver(self.scheduler, blackboard=blackboard)
                proponent = self.registry.load_agent(kwargs.get("proponent_id", "v1_gamma_proponent"))
                adversary = self.registry.load_agent(kwargs.get("adversary_id", "v1_gamma_adversary"))
                await solver.run_optimization_cycle(proponent, adversary)
            
            self._last_activity_time = time.time()
            logger.info(f"Session {run_type} completed successfully.")
            
            if kwargs.get("auto_consolidate", True):
                payload_path = self.consolidation.extract_validated_traces(blackboard, blackboard.topic[:10])
                if payload_path:
                    await self.consolidation.trigger_training(payload_path, "gemma-9b-schiz")
                    
        except Exception as e:
            logger.error(f"Session failed: {e}")
            await blackboard.add_entry(sender="SYSTEM", content=f"ERROR: {str(e)}")
        finally:
            self._last_activity_time = time.time()

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

