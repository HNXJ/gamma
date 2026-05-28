import sys, os, json, time, hashlib, glob
from datetime import datetime

# scripts/live_game_loop_32_stances.py - Continuous Live Gamma Labyrinth 32-Stance World

sys.path.append("/Users/HN/gamma-world/repos/gamma/src")
from gamma_runtime.lms_interface import (
    LMSInterface, LMSProviderSpec, LMSModelSpec, LMSCompletionRequest
)
from gamma_runtime.player_turn_contract_normalizer import PlayerTurnNormalizer

STANCES = ["scout", "patchsmith", "toolmaker", "trader", "archivist", "scientist_scaffold", "critic_judgelet", "sandbox_curator"]
BACKENDS = [
    ("mistralai_ministral-3-14b-instruct-2512-mlx", "mistral"),
    ("gemma-4-e4b-it-optiq", "gemma_optiq"),
    ("granite-4.1-30b", "granite"),
    ("gemma-4-e4b-it", "gemma_e4b")
]

class ContinuousWorld:
    def __init__(self, resume_dir=None):
        self.provider = LMSProviderSpec(
            provider_id="office_mac_lms", role="live_game_backend",
            base_url="http://127.0.0.1:1234/v1", route_ready=True, timeout_seconds=90,
            models=[LMSModelSpec(model_id=m[0], model_family="generic", model_label=m[1], route_ready=True) for m in BACKENDS]
        )
        self.interface = LMSInterface(providers=[self.provider])

        self.enable_normalizer = os.getenv("GAMMA_ENABLE_PLAYER_TURN_NORMALIZER", "0") == "1"
        if self.enable_normalizer:
            self.normalizer = PlayerTurnNormalizer()

        if resume_dir and os.path.exists(resume_dir):

            self.output_dir = resume_dir
            self.timestamp = os.path.basename(resume_dir)
            with open(os.path.join(resume_dir, "checkpoint_latest.json"), "r") as f:
                self.state = json.load(f)
            with open(os.path.join(resume_dir, "game_config.json"), "r") as f:
                config = json.load(f)
                self.players = config["roster"]
        else:
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = f"outputs/gamma_labyrinth/live_continuous_32_stance_game/{self.timestamp}"
            os.makedirs(self.output_dir, exist_ok=True)
            self.players = []
            for b_id, b_slug in BACKENDS:
                for stance in STANCES:
                    self.players.append({
                        "player_id": f"{b_slug}.{stance}", "model_id": b_id, "stance": stance,
                        "inventory": {"tools":[], "resources":[], "contributions":0},
                    })
            self.state = {
                "game_id": f"continuous-32-stance-{self.timestamp}",
                "current_turn": 38, "cycle_count": 0,
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

                turn_filename = f"turn_{turn_id:04d}_{p_id}.txt"
                turn_path = os.path.join(self.output_dir, turn_filename)
                with open(turn_path, "w") as f:
                    f.write(content)

                # --- Normalizer Integration ---
                if self.enable_normalizer:
                    try:
                        try:
                            json_str = content.replace("```json", "").replace("```", "").strip()
                            start = json_str.find("{")
                            end = json_str.rfind("}")
                            if start != -1 and end != -1:
                                json_str = json_str[start:end+1]
                            raw_turn = json.loads(json_str)
                        except Exception:
                            raw_turn = {"content": content}

                        raw_turn["player"] = p_id
                        raw_turn["stance"] = stance

                        normalized = self.normalizer.normalize(raw_turn)

                        log_entry = {
                            "source_turn_path": turn_path,
                            "player": p_id,
                            "turn_number": turn_id,
                            "model_backend": player["model_id"],
                            "canonical_stance": normalized.get("canonical_stance", ""),
                            "normalization_status": normalized.get("normalization_status", ""),
                            "domain_guard_status": normalized.get("domain_guard_status", ""),
                            "warnings": normalized.get("warnings", []) + normalized.get("domain_guard_warnings", []),
                            "errors": normalized.get("errors", []) + normalized.get("domain_guard_errors", []),
                            "truth_status": normalized.get("truth_status", "")
                        }

                        norm_path = os.path.join(self.output_dir, "normalized_turns.jsonl")
                        with open(norm_path, "a") as f:
                            f.write(json.dumps(log_entry) + "\n")

                        if normalized.get("normalization_status") == "rejected" or normalized.get("domain_guard_status") == "rejected":
                            reject_path = os.path.join(self.output_dir, "rejected_turns.jsonl")
                            with open(reject_path, "a") as f:
                                f.write(json.dumps(log_entry) + "\n")

                        if normalized.get("warnings") or normalized.get("domain_guard_warnings"):
                            warn_path = os.path.join(self.output_dir, "normalizer_warnings.jsonl")
                            with open(warn_path, "a") as f:
                                f.write(json.dumps(log_entry) + "\n")

                    except Exception as e:
                        err_path = os.path.join(self.output_dir, "normalizer_errors.jsonl")
                        with open(err_path, "a") as f:
                            f.write(json.dumps({
                                "source_turn_path": turn_path,
                                "player": p_id,
                                "turn_number": turn_id,
                                "error": str(e),
                                "raw_content": content
                            }) + "\n")
                # --- End Normalizer Integration ---
                self.state["current_turn"] += 1
            else:
                print(f"Failure for {p_id}")

            # Write heartbeat
            with open(f"{self.output_dir}/heartbeats.jsonl", "a") as f:
                f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "player": p_id, "turn": turn_id}) + "\n")

        self.state["cycle_count"] += 1
        with open(f"{self.output_dir}/checkpoint_latest.json", "w") as f:
            json.dump(self.state, f, indent=2)
        self._write_config()

        # Log cycle records
        with open(f"{self.output_dir}/turn_records.jsonl", "a") as f:
            for rec in cycle_records:
                f.write(json.dumps(rec) + "\n")

        if self.state["cycle_count"] % 10 == 0:
            self.update_hashes()

    def update_hashes(self):
        os.system(f"cd {self.output_dir} && find . -type f -not -name 'hashes.sha256' -exec shasum -a 256 {{}} + > hashes.sha256")

def get_latest_run_dir():
    base_dir = "outputs/gamma_labyrinth/live_continuous_32_stance_game"
    if not os.path.exists(base_dir): return None
    dirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    return sorted(dirs)[-1] if dirs else None

if __name__ == "__main__":
    resume_dir = None
    if "--resume" in sys.argv:
        if "auto" in sys.argv:
            resume_dir = get_latest_run_dir()
        else:
            idx = sys.argv.index("--resume")
            if idx + 1 < len(sys.argv) and not sys.argv[idx+1].startswith("--"):
                resume_dir = sys.argv[idx+1]

    world = ContinuousWorld(resume_dir=resume_dir)
    # Loop forever
    while True:
        world.run_cycle()
