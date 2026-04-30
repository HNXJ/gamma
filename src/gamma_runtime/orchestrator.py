import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List
from .types import AgentId, InferenceRequest, MissionContext
from .scheduler import InferenceScheduler
from .blackboard import Blackboard
from .registry import RuntimeRegistry
from .consolidation import ConsolidationManager
from apps.v1_gamma_sde_app import V1GammaSDEOrchestrator
from apps.council_app import CouncilOrchestrator
from sde_engine.solver import SDESolver
from sde_engine.adapter import ExecutionAdapter
from gamma.got.engine.persistence import ArenaPersistence
from .events import EventEmitter

logger = logging.getLogger("UnifiedOrchestrator")

class UnifiedOrchestrator:
    """
    The High-Level Controller for the Gamma Scientific Stack.
    Bridges Linguistic (Council) and Biophysical (SDE) reasoning.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, 
                 emitter: Optional[EventEmitter] = None,
                 tool_routers: Optional[Dict[str, Any]] = None,
                 context_hydrator: Optional[Any] = None):
        self.scheduler = scheduler
        self.registry = registry
        self.emitter = emitter
        self.tool_routers = tool_routers or {}
        self.context_hydrator = context_hydrator
        self.consolidation = ConsolidationManager()
        self.persistence = ArenaPersistence(game_id="game001", root_dir=str(registry.root.parent))
        self.adapter = ExecutionAdapter(proposals_dir=os.path.join(str(registry.root.parent), "data", "sde_proposals"))
        self._active_sessions: Dict[str, Blackboard] = {}
        self._last_activity_time = time.time()
        self._monitor_task: Optional[asyncio.Task] = None
        self._heartbeat_config: Dict[str, Any] = {
            "team_id": "v1_gamma_sde_team",
            "topic": "Autonomous SDE Refinement",
            "active": False
        }
        self._mission_context: Optional[MissionContext] = None

    def start_heartbeat_monitor(self, team_id: str = "v1_gamma_sde_team", topic: str = "Autonomous SDE Refinement"):
        """Activates the aggressive zero-idle-time heartbeat rule."""
        self._heartbeat_config["team_id"] = team_id
        self._heartbeat_config["topic"] = topic
        self._heartbeat_config["active"] = True
        
        if not self._monitor_task or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._heartbeat_loop())
            logger.info(f"💓 Heartbeat Monitor Activated: Team={team_id}")

    async def _heartbeat_loop(self):
        while self._heartbeat_config["active"]:
            now = time.time()
            idle_duration = now - self._last_activity_time
            
            if idle_duration > 1.0:
                try:
                    session_id = "heartbeat-session"
                    if session_id not in self._active_sessions:
                        self._active_sessions[session_id] = Blackboard(self._heartbeat_config["topic"])
                    
                    blackboard = self._active_sessions[session_id]
                    self._last_activity_time = now 
                    
                    self._mission_context = self._load_mission_context()
                    topic = self._mission_context.mission_topic
                    
                    orchestrator = V1GammaSDEOrchestrator(
                        self.scheduler, 
                        self.registry, 
                        mission_context=self._mission_context,
                        blackboard=blackboard,
                        tool_routers=self.tool_routers,
                        context_hydrator=self.context_hydrator
                    )
                    await orchestrator.run_deliberation(
                        team_id=self._heartbeat_config["team_id"],
                        topic=topic,
                        rounds=1
                    )
                    self._last_activity_time = time.time()
                except Exception as e:
                    logger.error(f"Heartbeat trigger failed: {e}")
                    await asyncio.sleep(5)
            await asyncio.sleep(0.5)

    async def launch_run(self, run_type: str, topic: str, **kwargs) -> str:
        session_id = f"session-{run_type}-{int(time.time())}"
        blackboard = Blackboard(topic)
        self._active_sessions[session_id] = blackboard
        
        if self.emitter:
            self.emitter.emit(
                agent_id="SYSTEM",
                role="orchestrator",
                event_type="turn_start",
                summary=f"Orchestrator launched {run_type} run on topic: {topic}",
                status="OK"
            )
            
        asyncio.create_task(self._execute_run(run_type, blackboard, **kwargs))
        return session_id

    async def _execute_run(self, run_type: str, blackboard: Blackboard, **kwargs):
        try:
            self._last_activity_time = time.time()
            if run_type == "council":
                orchestrator = CouncilOrchestrator(
                    self.scheduler, 
                    self.registry, 
                    blackboard=blackboard,
                    tool_routers=self.tool_routers,
                    context_hydrator=self.context_hydrator
                )
                await orchestrator.run_deliberation(
                    team_id=kwargs.get("team_id", "sde_debate_team"),
                    topic=blackboard.topic,
                    rounds=kwargs.get("rounds", 2)
                )
            elif run_type == "sde":
                # Ensure we have mission context for SDE runs
                mission_ctx = kwargs.get("mission_context") or self._load_mission_context()
                orchestrator = V1GammaSDEOrchestrator(
                    self.scheduler, 
                    self.registry, 
                    mission_context=mission_ctx, 
                    blackboard=blackboard,
                    tool_routers=self.tool_routers,
                    context_hydrator=self.context_hydrator
                )
                await orchestrator.run_deliberation(
                    team_id=kwargs.get("team_id", "v1_gamma_sde_team"),
                    topic=blackboard.topic,
                    rounds=kwargs.get("rounds", 1)
                )
            
            self._last_activity_time = time.time()
            logger.info(f"Session {run_type} completed successfully.")
        except Exception as e:
            logger.error(f"Session failed: {e}")
            await blackboard.add_entry(sender="SYSTEM", content=f"ERROR: {str(e)}")
        finally:
            self._last_activity_time = time.time()

    def _load_mission_context(self) -> MissionContext:
        try:
            board_path = self.registry.root / "patches" / "arena_patch_board.json"
            if not board_path.exists():
                return MissionContext(target_neuron_count=11, mission_topic="Default Substrate Review", patch_id="p001")
                
            import json
            with open(board_path, "r") as f:
                board = json.load(f)
                
            return MissionContext(
                target_neuron_count=board.get("active_mission_target", 11),
                mission_topic=board.get("active_mission_topic", "Substrate Review"),
                patch_id=board.get("active_patches", ["p001"])[0]
            )
        except Exception as e:
            logger.error(f"Mission Context load failure: {e}")
            return MissionContext(target_neuron_count=11, mission_topic="Fallback Mission", patch_id="pfallback")

    def get_all_sessions(self) -> List[Dict[str, Any]]:
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
