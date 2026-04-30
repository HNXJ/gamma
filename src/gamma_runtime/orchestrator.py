import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from .types import AgentId, InferenceRequest, MissionContext
from .scheduler import InferenceScheduler
from .blackboard import Blackboard
from .registry import RuntimeRegistry
from .consolidation import ConsolidationManager
from apps.v1_gamma_sde_app import V1GammaSDEOrchestrator
from sde_engine.solver import SDESolver
from sde_engine.adapter import ExecutionAdapter
from gamma.got.engine.persistence import ArenaPersistence
from .events import EventEmitter

logger = logging.getLogger("UnifiedOrchestrator")

class UnifiedOrchestrator:
    """
    The High-Level Controller for the Gamma Scientific Stack.
    Bridges Linguistic (Council) and Biophysical (SDE) reasoning.
    Now includes an aggressive Zero-Idle Heartbeat Monitor.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, emitter: Optional[EventEmitter] = None):
        self.scheduler = scheduler
        self.registry = registry
        self.emitter = emitter
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
                    
                    # Ensure we have a fresh mission context for each loop iteration
                    self._mission_context = self._load_mission_context()
                    topic = self._mission_context.mission_topic
                    
                    orchestrator = V1GammaSDEOrchestrator(
                        self.scheduler, 
                        self.registry, 
                        mission_context=self._mission_context,
                        blackboard=blackboard
                    )
                    await orchestrator.run_deliberation(
                        team_id=self._heartbeat_config["team_id"],
                        topic=topic,
                        rounds=1
                    )

                    # --- Stage 2 Execution Bridge ---
                    # 1. Search blackboard for an accepted proposal
                    latest_entry = blackboard.get_latest_entry()
                    if latest_entry and latest_entry.metadata.get("kind") == "proposal_acceptance":
                        proposal_id = latest_entry.metadata.get("proposal_id")
                        logger.info(f"🔍 Mission Alignment Confirmed for {proposal_id}. Materializing...")
                        
                        try:
                            # 2. Materialization (Second Trust Boundary)
                            exec_config = self.adapter.materialize_proposal(proposal_id, self._mission_context)
                            
                            # 3. Solver Execution
                            solver = SDESolver(self.scheduler, blackboard=blackboard, registry=self.registry)
                            state_entry = await solver.execute_materialized_config(exec_config)
                            
                            # 4. Success Verification & Persistence Commitment
                            if self.adapter.verify_substrate_success(state_entry.metadata, self._mission_context.target_neuron_count):
                                current_truth = self.persistence.get_state().get("largest_pass_network_neuron_count", 0)
                                if self._mission_context.target_neuron_count > current_truth:
                                    logger.info(f"🏆 MISSION SUCCESS: Leveling up substrate to N={self._mission_context.target_neuron_count}")
                                    self.persistence.save_state({
                                        "largest_pass_network_neuron_count": self._mission_context.target_neuron_count,
                                        "last_successful_patch": self._mission_context.patch_id
                                    })
                            else:
                                logger.warning(f"📉 Simulation failed to reach convergence or target count for {proposal_id}.")
                                
                        except Exception as exec_err:
                            logger.error(f"❌ Execution Bridge Failure: {exec_err}")
                            await blackboard.add_entry(
                                sender="SYSTEM_BRIDGE",
                                content=f"CRITICAL: Execution Bridge Failure: {str(exec_err)}"
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
                # Legacy path: defaults to unknown provenance, making it non-persistence-eligible
                await solver._run_optimization_cycle(proponent, adversary)
            
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
        # Mocking canonical G01-G04 if not present to ensure grid rendering
        if len(sessions) < 4:
            for i in range(len(sessions) + 1, 5):
                sessions.append({
                    "id": f"G0{i}",
                    "topic": "Standby",
                    "round": 0,
                    "last_active": None,
                    "status": "IDLE"
                })
        return sessions

    def _load_mission_context(self) -> MissionContext:
        """Fetches the current mission state from the active patch board. Fails closed if malformed."""
        try:
            board_path = self.registry.root / "patches" / "arena_patch_board.json"
            if not board_path.exists():
                raise FileNotFoundError(f"Mission target source missing: {board_path}")
                
            import json
            with open(board_path, "r") as f:
                board = json.load(f)
                
            topic = board.get("active_mission_topic")
            target = board.get("active_mission_target")
            
            if topic is None:
                raise ValueError("Mission topic missing from patch board.")
            if target is None or not isinstance(target, int):
                raise ValueError(f"Malformed or missing numeric mission target: {target}")
            
            # Determine active patch ID
            active_patches = board.get("active_patches", [])
            patch_id = active_patches[0] if active_patches else None
            
            return MissionContext(
                target_neuron_count=target,
                mission_topic=topic,
                patch_id=patch_id
            )
        except Exception as e:
            logger.critical(f"🛑 MISSION CONTEXT LOAD FAILURE: {e}")
            # In a fail-closed architecture, we could stop the system here.
            # For Stage 1, we raise so the heartbeat loop handles the failure.
            raise

    def _get_active_mission_topic(self) -> str:
        """Deprecated: Use _load_mission_context().mission_topic instead."""
        return self._load_mission_context().mission_topic

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
