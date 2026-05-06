import json
import os
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


class MockHarnessPlayer:
    """Deterministic player that returns pre-defined mock responses."""
    def __init__(self, player_id: str = "mock-player-01"):
        self.player_id = player_id
        self.responses = [
            "Mock response 1: I have inspected the SDE substrate and identified no pathological saturation.",
            "Mock response 2: Proposing a minor synaptic weight adjustment for the L4-L2/3 predictive loop."
        ]
        self.turn_index = 0

    def get_response(self, prompt: str) -> str:
        if self.turn_index < len(self.responses):
            response = self.responses[self.turn_index]
            self.turn_index += 1
            return response
        return "Mock response: End of deterministic sequence."


class HarnessSession:
    """Manages the lifecycle and artifact generation of a harness session."""
    def __init__(
        self,
        session_id: str,
        player_id: str,
        provider_id: str,
        model_id: str,
        role: str,
        artifact_dir: str,
        truth_mode: str = "truth_safe_unverified",
        truth_bearing_run: bool = False,
        continuity_banner: str = "",
        max_turns: int = 2
    ):
        self.session_id = session_id
        self.player_id = player_id
        self.provider_id = provider_id
        self.model_id = model_id
        self.role = role
        self.artifact_dir = Path(artifact_dir)
        self.truth_mode = truth_mode
        self.truth_bearing_run = truth_bearing_run
        self.continuity_banner = continuity_banner
        self.max_turns = max_turns
        self.turns: List[Dict[str, Any]] = []
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.artifact_hashes: Dict[str, str] = {}
        
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def redact(self, text: str) -> str:
        """Simple deterministic redaction of common secrets."""
        patterns = [
            (r"Bearer\s+[a-zA-Z0-9\._\-]+", "Bearer <REDACTED>"),
            (r"sk-[a-zA-Z0-9]{20,}", "sk-<REDACTED>"),
            (r"LM_STUDIO_API_KEY=[^\s]+", "LM_STUDIO_API_KEY=<REDACTED>"),
            (r"password=[^\s]+", "password=<REDACTED>"),
            (r"token=[^\s]+", "token=<REDACTED>")
        ]
        redacted = text
        for pattern, replacement in patterns:
            redacted = re.sub(pattern, replacement, redacted)
        return redacted

    def _compute_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def write_manifest(self):
        manifest = {
            "session_id": self.session_id,
            "player_id": self.player_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "role": self.role,
            "truth_mode": self.truth_mode,
            "truth_bearing_run": self.truth_bearing_run,
            "max_turns": self.max_turns,
            "started_at_utc": self.started_at,
            "artifact_policy": {
                "transcript_required": True,
                "sha256_required": True,
                "end_receipt_required": True,
                "redaction_required": True
            }
        }
        path = self.artifact_dir / "session_manifest.json"
        with open(path, "w") as f:
            json.dump(manifest, f, indent=2)
        self.artifact_hashes["session_manifest.json"] = self._compute_hash(path)

    def write_turn(self, turn_index: int, prompt: str, response: str):
        # Redact and apply banner check
        redacted_prompt = self.redact(prompt)
        redacted_response = self.redact(response)
        
        banner_inserted = False
        if turn_index == 1 and self.continuity_banner:
            if self.continuity_banner in prompt:
                banner_inserted = True

        turn_data = {
            "session_id": self.session_id,
            "turn_index": turn_index,
            "actor_id": self.player_id,
            "prompt_text_redacted": redacted_prompt,
            "response_text_redacted": redacted_response,
            "truth_mode": self.truth_mode,
            "truth_bearing_run": self.truth_bearing_run,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mock_transport": True,
            "continuity_banner_inserted_once": banner_inserted
        }
        self.turns.append(turn_data)
        
        # Write individual turn file
        turn_file = self.artifact_dir / f"turn_{turn_index:04d}.json"
        with open(turn_file, "w") as f:
            json.dump(turn_data, f, indent=2)
        self.artifact_hashes[turn_file.name] = self._compute_hash(turn_file)
        
        # Append to transcript.jsonl
        transcript_file = self.artifact_dir / "transcript.jsonl"
        with open(transcript_file, "a") as f:
            f.write(json.dumps(turn_data) + "\n")
        self.artifact_hashes["transcript.jsonl"] = self._compute_hash(transcript_file)

    def finalize(self, status: str = "COMPLETE"):
        receipt = {
            "session_id": self.session_id,
            "status": status,
            "turn_count": len(self.turns),
            "artifact_list": sorted(list(self.artifact_hashes.keys()) + ["artifact_hashes.sha256", "end_receipt.json"]),
            "hash_file_path": "artifact_hashes.sha256",
            "truth_mode": self.truth_mode,
            "truth_bearing_run": self.truth_bearing_run,
            "validation_summary": {
                "biological_truth_asserted": False,
                "player_participation_ready": False
            }
        }
        receipt_path = self.artifact_dir / "end_receipt.json"
        with open(receipt_path, "w") as f:
            json.dump(receipt, f, indent=2)
        
        # Update hashes one last time for the final files
        self.artifact_hashes["end_receipt.json"] = self._compute_hash(receipt_path)
        
        hash_path = self.artifact_dir / "artifact_hashes.sha256"
        with open(hash_path, "w") as f:
            for filename, h in sorted(self.artifact_hashes.items()):
                f.write(f"{h}  {filename}\n")


def validate_session_artifacts(artifact_dir: str) -> Dict[str, Any]:
    path = Path(artifact_dir)
    results = {
        "manifest_exists": (path / "session_manifest.json").exists(),
        "transcript_exists": (path / "transcript.jsonl").exists(),
        "receipt_exists": (path / "end_receipt.json").exists(),
        "hash_file_exists": (path / "artifact_hashes.sha256").exists(),
        "hashes_match": True,
        "secrets_found": False,
        "truth_bearing_run_false": False,
        "truth_mode_valid": False,
        "errors": []
    }
    
    if not results["hash_file_exists"]:
        results["hashes_match"] = False
    else:
        with open(path / "artifact_hashes.sha256", "r") as f:
            for line in f:
                parts = line.strip().split("  ")
                if len(parts) != 2: continue
                expected_h, filename = parts
                actual_h = hashlib.sha256(open(path / filename, "rb").read()).hexdigest()
                if expected_h != actual_h:
                    results["hashes_match"] = False
                    results["errors"].append(f"Hash mismatch: {filename}")

    # Check manifest for truth mode
    if results["manifest_exists"]:
        with open(path / "session_manifest.json", "r") as f:
            manifest = json.load(f)
            results["truth_bearing_run_false"] = manifest.get("truth_bearing_run") is False
            results["truth_mode_valid"] = manifest.get("truth_mode") == "truth_safe_unverified"

    # Simple secret scan
    secret_patterns = [r"Bearer\s+", r"sk-", r"API_KEY", r"password", r"token"]
    for file in path.glob("*"):
        if file.suffix in [".json", ".jsonl", ".sha256"]:
            with open(file, "r", errors="ignore") as f:
                content = f.read()
                # Check if unredacted secrets exist
                if any(re.search(p, content) for p in secret_patterns):
                    # But ignore the redaction placeholders themselves
                    unredacted = False
                    if "Bearer " in content and "Bearer <REDACTED>" not in content: unredacted = True
                    if "sk-" in content and "sk-<REDACTED>" not in content: unredacted = True
                    # This is a very coarse check for self-test purposes
                    if unredacted:
                        results["secrets_found"] = True
                        results["errors"].append(f"Potential unredacted secret in {file.name}")

    return results


def run_self_test():
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Starting self-test in {tmp_dir}")
        session_id = "test-session-001"
        banner = "# Continuity Banner Test"
        
        session = HarnessSession(
            session_id=session_id,
            player_id="mock-player",
            provider_id="mock-provider",
            model_id="mock-model",
            role="tester",
            artifact_dir=tmp_dir,
            continuity_banner=banner
        )
        
        player = MockHarnessPlayer()
        
        session.write_manifest()
        
        # Turn 1
        prompt1 = banner + "\nTell me about the substrate."
        response1 = player.get_response(prompt1)
        session.write_turn(1, prompt1, response1)
        
        # Turn 2
        prompt2 = "What about weights?"
        response2 = player.get_response(prompt2)
        session.write_turn(2, prompt2, response2)
        
        session.finalize()
        
        validation = validate_session_artifacts(tmp_dir)
        print("Validation Results:")
        print(json.dumps(validation, indent=2))
        
        if all([validation["manifest_exists"], validation["transcript_exists"], 
                validation["receipt_exists"], validation["hash_file_exists"], 
                validation["hashes_match"], not validation["secrets_found"]]):
            print("SELF-TEST PASSED")
            return 0
        else:
            print("SELF-TEST FAILED")
            return 1


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        sys.exit(run_self_test())
    else:
        print("Gamma Mock Harness Artifact Logic Loaded. Use --self-test to verify.")
