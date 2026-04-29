import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from .structs import AgentId, InferenceRequest
from .scheduler import InferenceScheduler
from .blackboard import Blackboard
from .registry import RuntimeRegistry
from .consolidation import ConsolidationManager
from .idle_review import IdleReviewManager
from .heartbeat_state import HeartbeatManager
from apps.council_app import CouncilOrchestrator

logger = logging.getLogger("UnifiedOrchestrator")

class UnifiedOrchestrator:
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry):
        self.scheduler = scheduler
        self.registry = registry
        self.consolidation = ConsolidationManager()
        self._active_sessions: Dict[str, Blackboard] = {}
        self.root = Path('/Users/HN/MLLM/gamma')
        self.heartbeat = HeartbeatManager(self.root)
        self.idle_review_managers: Dict[str, IdleReviewManager] = {}

    async def launch_run(self, run_type: str, topic: str, **kwargs) -> str:
        game_id = kwargs.pop("game_id", f"game-{int(asyncio.get_event_loop().time())}")
        
        (self.root / 'local' / game_id / 'logs').mkdir(parents=True, exist_ok=True)
        (self.root / 'local' / game_id / 'notes' / 'heartbeat' / 'inputs').mkdir(parents=True, exist_ok=True)
        (self.root / 'local' / game_id / 'notes' / 'heartbeat' / 'outputs').mkdir(parents=True, exist_ok=True)
        
        blackboard = Blackboard(topic)
        self._active_sessions[game_id] = blackboard
        
        self.idle_review_managers[game_id] = IdleReviewManager(
            self.scheduler, self.registry, self.heartbeat, game_id, self.root
        )
        
        if not hasattr(self, '_idle_loop_task'):
            self._idle_loop_task = asyncio.create_task(self._idle_monitoring_loop())

        asyncio.create_task(self._execute_run(run_type, blackboard, game_id=game_id, **kwargs))
        
        return game_id

    async def _execute_run(self, run_type: str, blackboard: Blackboard, game_id: str, **kwargs):
        try:
            if run_type == "council":
                orchestrator = CouncilOrchestrator(
                    self.scheduler, 
                    self.registry, 
                    self.heartbeat,
                    blackboard=blackboard,
                    game_id=game_id
                )
                await orchestrator.run_deliberation(
                    team_id=kwargs.get("team_id", "v1_gamma_sde_team"),
                    topic=blackboard.topic,
                    rounds=kwargs.get("rounds", 1)
                )
            logger.info(f"Session {game_id} ({run_type}) completed.")
        except Exception as e:
            logger.error(f"Session {game_id} failed: {e}")

    async def _idle_monitoring_loop(self):
        logger.info("Idle monitoring loop started (Rule: Continuous activity for persistent missions).")
        while True:
            await asyncio.sleep(15) 
            
            now = time.time()
            hb_state = self.heartbeat.get_state()
            last_real = hb_state.get('last_real_task_time', 0)
            
            for game_id, manager in list(self.idle_review_managers.items()):
                is_persistent = self._check_if_persistent(game_id)
                
                # If persistent, we want near 100% agent activity.
                threshold = 30 if is_persistent else 300
                cadence = 45 if is_persistent else 900
                
                idle_duration = now - last_real
                
                if idle_duration >= threshold:
                    if now - manager.last_idle_review_time >= cadence:
                        if not self._is_proposal_running(game_id):
                            logger.info(f"Persistent mission {game_id} idle for {idle_duration:.1f}s. Triggering heartbeat.")
                            await manager.run_heartbeat(idle_duration)

    def _check_if_persistent(self, game_id: str) -> bool:
        state_path = self.root / 'local' / game_id / 'arena_season_state.json'
        if state_path.exists():
            try:
                with open(state_path, 'r') as f:
                    state = json.load(f)
                    return "grow to" in state.get("objective", "").lower()
            except: pass
        return False

    def _is_proposal_running(self, game_id: str) -> bool:
        topology = self.idle_review_managers[game_id].topology
        if topology.proposals_file.exists():
            with open(topology.proposals_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get('status') == 'running':
                            return True
                    except: continue
        return False

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        blackboard = self._active_sessions.get(session_id)
        if not blackboard: return None
        hb_state = self.heartbeat.get_state()
        now = time.time()
        idle_duration = now - hb_state.get('last_real_task_time', 0)
        return {
            "session_id": session_id,
            "topic": blackboard.topic,
            "system_status": "IDLE" if idle_duration > 300 else "ACTIVE",
            "idle_duration": idle_duration
        }
