import json
import os
import asyncio
import logging
import time
from datetime import datetime
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
    Now includes an aggressive Zero-Idle Heartbeat Monitor and first-class Persistence.
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
        
        # Persistence Metadata
        self.checkpoint_path = "local/arena_checkpoint.json"
        self.last_checkpoint_time: Optional[float] = None
        self.resume_count: int = 0
        self.boot_type: str = "FRESH"
        self.last_resume_time: Optional[float] = None
        
        # Try to resume on startup
        self.load_checkpoint()

    def save_checkpoint(self):
        """Persists the entire arena state to disk."""
        try:
            state = {
                "timestamp": time.time(),
                "resume_count": self.resume_count,
                "sessions": {sid: bb.to_dict() for sid, bb in self._active_sessions.items()},
                "heartbeat_config": self._heartbeat_config
            }
            os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
            with open(self.checkpoint_path, 'w') as f:
                json.dump(state, f, indent=2)
            self.last_checkpoint_time = time.time()
            logger.info(f"💾 Checkpoint saved to {self.checkpoint_path}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self):
        """Restores arena state from the last known checkpoint."""
        if not os.path.exists(self.checkpoint_path):
            logger.info("No checkpoint found. Starting fresh.")
            return

        try:
            with open(self.checkpoint_path, 'r') as f:
                state = json.load(f)
            
            self.resume_count = state.get("resume_count", 0) + 1
            self.boot_type = "RESUMED"
            self.last_resume_time = time.time()
            self._heartbeat_config = state.get("heartbeat_config", self._heartbeat_config)
            
            for sid, bb_data in state.get("sessions", {}).items():
                self._active_sessions[sid] = Blackboard.from_dict(bb_data)
            
            logger.info(f"🔄 Arena Resumed from {self.checkpoint_path} (Resume Count: {self.resume_count})")
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            self.boot_type = "RECOVERY_FAILED"

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
                    session_id = "heartbeat-session"
                    if session_id not in self._active_sessions:
                        self._active_sessions[session_id] = Blackboard(self._heartbeat_config["topic"])
                    
                    blackboard = self._active_sessions[session_id]
                    self._last_activity_time = now 
                    
                    orchestrator = CouncilOrchestrator(self.scheduler, self.registry, blackboard=blackboard)
                    await orchestrator.run_deliberation(
                        team_id=self._heartbeat_config["team_id"],
                        topic=blackboard.topic,
                        rounds=1
                    )
                    self._last_activity_time = time.time()
                except Exception as e:
                    logger.error(f"Heartbeat trigger failed: {e}")
                    await asyncio.sleep(5)
                finally:
                    self.save_checkpoint() # Save after heartbeat
            
            await asyncio.sleep(0.5)

    async def launch_run(self, run_type: str, topic: str, **kwargs) -> str:
        session_id = f"session-{run_type}-{int(time.time())}"
        blackboard = Blackboard(topic)
        self._active_sessions[session_id] = blackboard
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
            
            self.save_checkpoint() # Auto-checkpoint after successful run
                    
        except Exception as e:
            logger.error(f"Session failed: {e}")
            await blackboard.add_entry(sender="SYSTEM", content=f"ERROR: {str(e)}")
        finally:
            self._last_activity_time = time.time()

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Returns a list of all active sessions for the dashboard matrix."""
        sessions = []
        for sid, bb in self._active_sessions.items():
            sessions.append({
                "id": sid,
                "topic": bb.topic,
                "round": bb.round,
                "last_active": bb.entries[-1].timestamp.isoformat() if bb.entries else None,
                "status": "DELIBERATING" if sid == "heartbeat-session" else "ACTIVE"
            })
        return sessions

    def get_persistence_status(self) -> Dict[str, Any]:
        """Exposes persistence metadata for the operator dashboard."""
        return {
            "boot_type": self.boot_type,
            "resume_count": self.resume_count,
            "last_checkpoint": datetime.fromtimestamp(self.last_checkpoint_time).isoformat() if self.last_checkpoint_time else "NEVER",
            "last_resume": datetime.fromtimestamp(self.last_resume_time).isoformat() if self.last_resume_time else "NEVER",
            "checkpoint_path": self.checkpoint_path,
            "freshness": "GROUNDED" if self.last_checkpoint_time and (time.time() - self.last_checkpoint_time < 60) else "DEGRADED"
        }

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
