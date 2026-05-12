import asyncio
import time
import json
import os
import argparse
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from .runtime_types import AgentSpec, InferenceRequest, InferenceResult, ModelSpec
from .registry import RuntimeRegistry
from .scheduler import InferenceScheduler
from .model_profiles import ProfileRegistry

class AutoContinueDaemon:
    """
    Minimal safe-mode turn daemon for Gamma Labyrinth.
    Dispatches bounded non-science turns to route-safe agents.
    """
    def __init__(
        self, 
        registry: RuntimeRegistry,
        scheduler: InferenceScheduler,
        interval_sec: int = 60,
        max_turns: int = 3,
        dry_run: bool = True,
        target_agents: Optional[List[str]] = None
    ):
        self.registry = registry
        self.scheduler = scheduler
        self.interval_sec = interval_sec
        self.max_turns = max_turns
        self.dry_run = dry_run
        self.target_agents = target_agents
        self.run_id = f"auto-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        self.output_dir = Path("outputs/gamma_labyrinth/auto_continue") / self.run_id
        
        # Load profile registry to check route-readiness
        self.profiles = ProfileRegistry()
        self._initialize_default_profiles()

    def _initialize_default_profiles(self):
        """Initializes the profile registry with Phase 2 safe defaults."""
        from .model_profiles import ModelProfile
        
        # gemma4-parallel is the current baseline for Phase 2
        self.profiles.register(ModelProfile(
            profile_id="gemma4-parallel",
            host="office-mac",
            base_url="http://100.69.184.42:1234/v1",
            gamma_display_name="gemma-4-e4b-it-mlx",
            lms_canonical_model_id="gemma-4-e4b-it", # Use base ID to avoid quarantine pattern 'mxfp8'
            profile_status="ready" # Explicitly ready for dry-run/smoke
        ))
        
        # Add gemma-9b-schiz as well
        self.profiles.register(ModelProfile(
            profile_id="gemma-9b-schiz",
            host="office-mac",
            base_url="http://100.69.184.42:1234/v1",
            gamma_display_name="gemma-2-9b-it-schiz-mlx",
            lms_canonical_model_id="gemma-2-9b-it",
            profile_status="ready"
        ))

    def plan_eligible_turns(self, team_id: str) -> List[AgentSpec]:
        """Selects agents that are route-safe and not load-blocked."""
        try:
            team_config = self.registry.load_team(team_id)
        except Exception as e:
            print(f"❌ Failed to load team {team_id}: {e}")
            return []
            
        eligible = []
        for agent_id in team_config.get("agents", []):
            # Apply agent filter if provided
            if self.target_agents and agent_id not in self.target_agents:
                continue

            try:
                agent = self.registry.load_agent(agent_id)
                model_spec = self.registry.load_model(agent.model_key)
                
                # Check if model is blocked
                profile = self.profiles.get_profile(model_spec.key)
                if profile.is_route_ready():
                    eligible.append(agent)
                else:
                    print(f"ℹ️ Agent {agent_id} skipped: Model profile {model_spec.key} is {profile.profile_status}")
            except Exception as e:
                print(f"⚠️ Error planning turn for agent {agent_id}: {e}")
                continue
                
        return eligible

    async def execute_tick(self, agents: List[AgentSpec]):
        """Executes one turn for the provided agents."""
        if not agents:
            return

        tick_id = int(time.time())
        results = []

        for agent in agents:
            if self.dry_run:
                # DRY-RUN: Do not call LMS
                result = InferenceResult(
                    text=f"[DRY-RUN] Sample response for {agent.agent_id}",
                    raw={"mode": "dry_run"},
                    usage={"tokens": 0},
                    latency_s=0.01
                )
            else:
                # LIVE: Call LMS through scheduler
                try:
                    profile = self.profiles.get_profile(agent.model_key)
                    
                    request = InferenceRequest(
                        session_id=f"{self.run_id}-{tick_id}",
                        agent_id=agent.agent_id,
                        model_key=agent.model_key,
                        model_id=profile.lms_canonical_model_id,
                        messages=[
                            {"role": "system", "content": agent.system_prompt},
                            {"role": "user", "content": "HEARTBEAT_CHECK: confirm readiness."}
                        ],
                        generation=agent.generation or {"max_tokens": 128},
                        adapter_stack=agent.adapter_stack
                    )
                    
                    result = await self.scheduler.schedule(agent.model_key, request)
                except Exception as e:
                    print(f"❌ Live turn failed for {agent.agent_id}: {e}")
                    result = InferenceResult(
                        text="[BACKEND_UNAVAILABLE] Agent paused due to routing/backend failure.",
                        raw={"error": str(e)},
                        usage={"tokens": 0},
                        latency_s=0.0
                    )

            results.append((agent.agent_id, result))
            
        self._persist_tick(tick_id, results)
        return results

    def _persist_tick(self, tick_id: int, results: List[tuple[str, InferenceResult]]):
        """Writes manifest and artifacts to the run directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "run_id": self.run_id,
            "tick_id": tick_id,
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "truth_mode": "truth_safe_unverified",
            "truth_bearing_run": False,
            "claims": {
                "model_load": not self.dry_run,
                "biological": False,
                "science_growth": False
            },
            "turns": []
        }

        for agent_id, res in results:
            turn_file = f"turn_{tick_id}_{agent_id}.json"
            
            # Identify if it's a backend failure
            is_unavailable = "[BACKEND_UNAVAILABLE]" in res.text
            
            turn_data = {
                "agent_id": agent_id,
                "text": res.text,
                "latency_s": res.latency_s,
                "usage": res.usage,
                "status": "paused/degraded" if is_unavailable else "live" if not self.dry_run else "dry_run"
            }
            
            with open(self.output_dir / turn_file, "w") as f:
                json.dump(turn_data, f, indent=2)
                
            manifest["turns"].append({
                "agent_id": agent_id,
                "artifact": turn_file,
                "hash": "sha256_placeholder"
            })

        with open(self.output_dir / f"manifest_{tick_id}.json", "w") as f:
            json.dump(manifest, f, indent=2)

    async def start(self, team_id: str):
        """Starts the main turn loop."""
        print(f"🚀 Starting Auto-Continue Daemon [Run ID: {self.run_id}]")
        print(f"   Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        print(f"   Interval: {self.interval_sec}s | Max Turns: {self.max_turns}")
        
        if not self.dry_run:
            # Register pools for live mode
            from .backend_lmstudio import LMStudioBackend
            from .model_pool import SharedModelPool
            
            for profile in self.profiles.route_ready_profiles():
                try:
                    model_spec = self.registry.load_model(profile.profile_id)
                    # LMStudioBackend adds /v1 itself
                    backend = LMStudioBackend(base_url=profile.base_url.replace("/v1", ""))
                    pool = SharedModelPool(model_spec, backend)
                    await self.scheduler.register_pool(pool)
                    print(f"✅ Registered live pool for {profile.profile_id}")
                except Exception as e:
                    print(f"⚠️ Failed to register pool for {profile.profile_id}: {e}")

        turns_taken = 0
        while turns_taken < self.max_turns:
            eligible = self.plan_eligible_turns(team_id)
            if not eligible:
                print("⚠️ No eligible route-safe agents found. Waiting...")
            else:
                print(f"⏱️ Dispatching tick {turns_taken + 1}/{self.max_turns}...")
                await self.execute_tick(eligible)
                turns_taken += 1
            
            if turns_taken < self.max_turns:
                await asyncio.sleep(self.interval_sec)
        
        print(f"🏁 Auto-Continue run {self.run_id} complete.")

async def main():
    parser = argparse.ArgumentParser(description="Gamma Auto-Continue Daemon")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Enable live backend-gated mode")
    parser.add_argument("--interval-sec", type=int, default=60)
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--team", type=str, default="gamma_structured_team")
    parser.add_argument("--agents", type=str, help="Comma-separated list of agent IDs to include")
    parser.add_argument("--config-root", type=str, default="context/configs")
    args = parser.parse_args()

    # If --live is provided, it overrides dry_run default
    dry_run = not args.live
    
    target_agents = args.agents.split(",") if args.agents else None

    registry = RuntimeRegistry(args.config_root)
    scheduler = InferenceScheduler()
    
    daemon = AutoContinueDaemon(
        registry=registry,
        scheduler=scheduler,
        interval_sec=args.interval_sec,
        max_turns=args.max_turns,
        dry_run=dry_run,
        target_agents=target_agents
    )
    
    await daemon.start(args.team)

if __name__ == "__main__":
    asyncio.run(main())
