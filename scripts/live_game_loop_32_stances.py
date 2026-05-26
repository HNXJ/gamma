import sys, os, json, time, hashlib
from datetime import datetime

# scripts/live_game_loop_32_stances.py - Continuous Live Gamma Labyrinth 32-Stance World

sys.path.append("/Users/HN/gamma-world/repos/gamma/src")
from gamma_runtime.lms_interface import (
    LMSInterface, LMSProviderSpec, LMSModelSpec, LMSCompletionRequest
)

STANCES = ["scout", "patchsmith", "toolmaker", "trader", "archivist", "scientist_scaffold", "critic_judgelet", "sandbox_curator"]
BACKENDS = [
    ("mistralai_ministral-3-14b-instruct-2512-mlx", "mistral"),
    ("gemma-4-e4b-it-optiq", "gemma_optiq"),
    ("granite-4.1-30b", "granite"),
    ("gemma-4-e4b-it", "gemma_e4b")
]

class ContinuousWorld:
    def __init__(self, resume_turn=38):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"outputs/gamma_labyrinth/live_continuous_32_stance_game/{self.timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.provider = LMSProviderSpec(
            provider_id="office_mac_lms", role="live_game_backend", 
            base_url="http://127.0.0.1:1234/v1", route_ready=True, timeout_seconds=90,
            models=[LMSModelSpec(model_id=m[0], model_family="generic", model_label=m[1], route_ready=True) for m in BACKENDS]
        )
        self.interface = LMSInterface(providers=[self.provider])
        self.players = []
        for b_id, b_slug in BACKENDS:
            for stance in STANCES:
                self.players.append({
                    "player_id": f"{b_slug}.{stance}", "model_id": b_id, "stance": stance,
                    "inventory": {"tools":[], "resources":[], "contributions":0},
                })
        
        self.state = {
            "game_id": f"continuous-32-stance-{self.timestamp}",
            "current_turn": resume_turn, "cycle_count": 0,
            "drift_count": 0, "truth_safety_failure_count": 0
        }
        self._write_config()

    def _write_config(self):
        with open(f"{self.output_dir}/game_config.json", "w") as f:
            json.dump({"state": self.state, "roster": self.players}, f, indent=2)

    def run_cycle(self):
        print(f"--- CYCLE {self.state['cycle_count']} (Turn {self.state['current_turn']}) ---")
        cycle_records = []
        
        # Load directives
        directive_summary = ""
        directives_path = f"{self.output_dir}/game_directives.jsonl"
        if os.path.exists(directives_path):
            try:
                with open(directives_path, "r") as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        latest_directive = json.loads(lines[-1])
                        directive_summary = f" ACTIVE DIRECTIVE: {latest_directive.get('message', '')}"
            except Exception as e:
                print(f"Error reading directives: {e}")
        
        for player in self.players:
            turn_id = self.state["current_turn"]
            p_id = player["player_id"]
            stance = player["stance"]
            
            prompt = (
                f"You are {p_id} ({stance}) in Gamma Labyrinth turn {turn_id}. "
                "Continuous scientific-runtime game. Stay inside data/literature analysis, biophysical modeling, "
                "simulation planning, hypothesis validation, tool/harness improvement, and sandbox resource evolution. "
                "Do not invent fictional world state. Contribute to the game: actions, patches, tools, trades, sandbox resources. "
                f"Output one short JSON: {{player_id, stance_id, action_type, contribution, patch_proposal_or_null, trade_offer_or_null, resource_request_or_null, truth_status: 'truth_safe_unverified', non_claims}}.{directive_summary}"
            )
            
            res = self.interface.complete(LMSCompletionRequest(
                provider_id="office_mac_lms", model_id=player["model_id"],
                messages=[{"role":"user", "content":prompt}], dry_run=False, max_tokens=256
            ))
            
            if res.success:
                content = res.content.strip()
                player["inventory"]["contributions"] += 1
                cycle_records.append({"turn_id": turn_id, "player_id": p_id, "content": content})
                with open(f"{self.output_dir}/turn_{turn_id:04d}_{p_id}.txt", "w") as f:
                    f.write(content)
                self.state["current_turn"] += 1
            else:
                print(f"Failure for {p_id}")
            
            # Write heartbeat
            with open(f"{self.output_dir}/heartbeats.jsonl", "a") as f:
                f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "player": p_id, "turn": turn_id}) + "\n")
        
        self.state["cycle_count"] += 1
        with open(f"{self.output_dir}/checkpoint_latest.json", "w") as f:
            json.dump(self.state, f, indent=2)
        
        # Log cycle records
        with open(f"{self.output_dir}/turn_records.jsonl", "a") as f:
            for rec in cycle_records:
                f.write(json.dumps(rec) + "\n")

        if self.state["cycle_count"] % 10 == 0:
            self.update_hashes()

    def update_hashes(self):
        os.system(f"cd {self.output_dir} && find . -type f -not -name 'hashes.sha256' -exec shasum -a 256 {{}} + > hashes.sha256")

if __name__ == "__main__":
    world = ContinuousWorld()
    # Run at least one full cycle (32 players)
    world.run_cycle()
    # Then loop forever (or for a few more cycles in this window)
    for _ in range(2):
        world.run_cycle()