import json
import os
import requests
import hashlib

class LMS8SlotHarness:
    def __init__(self, artifact_root, lms_url="http://100.69.184.42:1234/v1"):
        self.artifact_root = artifact_root
        self.lms_url = lms_url
        self.roles = ['receptionist', 'worker_alpha', 'worker_beta', 'critic', 'judge', 'redaction_auditor', 'receipt_verifier', 'synthesizer']

    def _ensure_dirs(self):
        os.makedirs(f"{self.artifact_root}/turn_requests", exist_ok=True)
        os.makedirs(f"{self.artifact_root}/turn_responses", exist_ok=True)

    def generate_manifest(self):
        self._ensure_dirs()
        manifest = []
        for i, role in enumerate(self.roles):
            instance_id = 'gemma-4-e4b-it-mlx' if i == 0 else f'gemma-4-e4b-it-mlx:{i+1}'
            req = {
                'model': instance_id,
                'messages': [
                    {'role': 'system', 'content': 'Gamma Labyrinth continuity. You are a harnessed LMS slot in a minimal protocol validation round. truth_mode: truth_safe_unverified. truth_bearing_run: false. No secrets. No biological/scientific truth claims. Output compact JSON only.'},
                    {'role': 'user', 'content': f'Return compact JSON with exactly these keys: ok, slot_id, role, lms_instance_id_seen, truth_mode, truth_bearing_run, protocol_understood, no_science_claims, next_action. Set slot_id=gamma_{i+1:02}, role={role}, lms_instance_id_seen={instance_id}, truth_mode=truth_safe_unverified, truth_bearing_run=false, protocol_understood=true, no_science_claims=true, next_action=end_minimal_harness_round'}
                ],
                'temperature': 0,
                'max_tokens': 160,
                'stream': False
            }
            manifest.append(req)
            with open(f"{self.artifact_root}/turn_requests/slot_{i+1:02}_{role}_request.json", 'w') as f:
                json.dump(req, f, indent=2)
        return manifest

    def execute_dry_run(self):
        print(f"Dry run: Would execute {len(self.roles)} calls to {self.lms_url}")
        # Validate manifest files exist
        for i, role in enumerate(self.roles):
            assert os.path.exists(f"{self.artifact_root}/turn_requests/slot_{i+1:02}_{role}_request.json")
        return True

    @staticmethod
    def parse_response(body):
        # Extract first JSON object using regex as a reliable fallback for nested/fenced outputs
        import re
        match = re.search(r'\{.*\}', body, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("No JSON found")

    def generate_receipt(self, results):
        receipt = {
            "phase": "office_mac_lms_8slot_contract_smoke",
            "completion_calls_made": len(results),
            "slots_accepted": sum(1 for r in results if r['status'] == 'ACCEPT'),
            "truth_mode": "truth_safe_unverified",
            "decision": "ACCEPT_8SLOT_CONTRACT_SMOKE"
        }
        with open(f"{self.artifact_root}/minimal_8slot_harness_round_receipt.json", 'w') as f:
            json.dump(receipt, f, indent=2)

        # Hashes
        with open(f"{self.artifact_root}/artifact_hashes.sha256", 'w') as f:
            for file in os.listdir(self.artifact_root):
                if file.endswith('.json'):
                    h = hashlib.sha256()
                    with open(f"{self.artifact_root}/{file}", 'rb') as f_in:
                        h.update(f_in.read())
                    f.write(f"{h.hexdigest()} {file}\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--artifact-root", required=True)
    args = parser.parse_args()

    harness = LMS8SlotHarness(args.artifact_root)
    harness.generate_manifest()
    if args.dry_run:
        harness.execute_dry_run()
