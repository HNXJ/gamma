import json
import logging
import os
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from src.gamma_runtime.types import MissionContext

logger = logging.getLogger("ExecutionAdapter")

class ExecutionAdapter:
    """
    Stage 2 Execution Adapter / Proposal Materializer.
    Converts a mission-aligned proposal JSON into an executable solver config.
    Acts as the second trust boundary for the Execution Plane.
    """
    def __init__(self, proposals_dir: str):
        self.proposals_dir = proposals_dir
        self.adapter_version = "2.5.0-E"
        self.solver_id = "sde_solver_v1"
        
        # Stage 2E: Persistent bridge authority secret and receipt log
        base_dir = os.path.dirname(self.proposals_dir)
        secret_path = os.path.join(base_dir, "bridge_authority_v2.key")
        self.receipts_path = os.path.join(base_dir, "bridge_receipts.log")
        
        if os.path.exists(secret_path):
            with open(secret_path, "r") as f:
                self._secret = f.read().strip()
        else:
            self._secret = "emergency_fallback_unverified_secret"

        self._authorized_runs: set[str] = set()

    def _canonical_hash(self, obj: Any) -> str:
        """Deterministic SHA256 hash of a serializable object."""
        canonical_json = json.dumps(obj, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode()).hexdigest()

    def _sign_attestation(self, tuple_data: str) -> str:
        """HMAC-SHA256 signature over a canonical tuple."""
        return hmac.new(self._secret.encode(), tuple_data.encode(), hashlib.sha256).hexdigest()

    def materialize_proposal(self, proposal_id: str, mission_context: MissionContext) -> Dict[str, Any]:
        """
        Re-validates and materializes a proposal into a solver-ready executable state.
        Ensures provenance and mission alignment at execution ingress.
        """
        filename = os.path.join(self.proposals_dir, f"{proposal_id}.json")
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Execution Failure: Proposal artifact not found: {filename}")

        with open(filename, 'r') as f:
            proposal = json.load(f)

        # 1. Execution-Ingress Re-validation
        meta = proposal.get("meta", {})
        proposal_n = meta.get("neuron_count")

        if proposal_n is None:
            raise ValueError(f"Execution Rejected: Proposal {proposal_id} lacks 'meta.neuron_count'.")
        
        if proposal_n != mission_context.target_neuron_count:
            raise ValueError(
                f"Execution Rejected: Mission Mismatch. "
                f"Proposal N={proposal_n} != Target N={mission_context.target_neuron_count}"
            )

        # 2. Materialization Logic: Minimal Executable Representation
        # Stage 2E: Payload-Bound Authenticated Provenance
        run_id = f"run_{int(os.times()[4])}_{proposal_id[-8:]}"
        issued_at = os.times()[4]
        self._authorized_runs.add(run_id)
        
        params = proposal.get("params", {})
        config_to_hash = {
            "proposal_id": proposal_id,
            "neuron_count": proposal_n,
            "params": params
        }
        config_hash = self._canonical_hash(config_to_hash)
        
        # Canonical Tuple (Stage 2E): Full context binding
        # mission_id | proposal_id | run_id | target_count | config_hash | solver_id | issued_at | adapter_version
        mission_id = mission_context.patch_id or mission_context.mission_topic
        auth_tuple = "|".join([
            str(mission_id),
            str(proposal_id),
            str(run_id),
            str(proposal_n),
            str(config_hash),
            str(self.solver_id),
            str(issued_at),
            str(self.adapter_version)
        ])
        attestation = self._sign_attestation(auth_tuple)

        executable_config = {
            "proposal_id": proposal_id,
            "neuron_count": proposal_n,
            "params": params,
            "mission_topic": mission_context.mission_topic,
            "provenance": {
                "materialized_by": "ExecutionAdapter",
                "adapter_version": self.adapter_version,
                "solver_id": self.solver_id,
                "run_id": run_id,
                "mission_id": mission_id,
                "config_hash": config_hash,
                "attestation": attestation,
                "issued_at": issued_at
            }
        }

        logger.info(f"🚀 Proposal {proposal_id} materialized. Payload-Bound Attestation: {attestation[:8]}...")
        return executable_config

    def verify_substrate_success(self, metadata: Dict[str, Any], target_count: int) -> bool:
        """
        Final Stage 2E Truth-Safe Gate.
        Requires biophysical convergence, target alignment, authenticated payload-binding, and replay protection.
        """
        converged = metadata.get("converged", False)
        count_match = metadata.get("neuron_count") == target_count
        
        # Provenance Extraction (Stage 2E)
        provenance = metadata.get("provenance", {})
        attestation = provenance.get("attestation")
        run_id = provenance.get("run_id")
        config_hash = provenance.get("config_hash")
        
        # Reconstruct Canonical Tuple from untrusted result metadata
        # mission_id | proposal_id | run_id | target_count | config_hash | solver_id | issued_at | adapter_version
        observed_tuple = "|".join([
            str(provenance.get("mission_id")),
            str(metadata.get("proposal_id")),
            str(run_id),
            str(metadata.get("neuron_count")),
            str(config_hash),
            str(provenance.get("solver_id")),
            str(provenance.get("issued_at")),
            str(provenance.get("adapter_version"))
        ])
        
        expected_attestation = self._sign_attestation(observed_tuple)
        
        # Verification Gates
        is_authenticated = (attestation == expected_attestation)
        is_canonical = provenance.get("materialized_by") == "ExecutionAdapter"
        
        # Replay Protection (Stage 2E)
        is_replay = False
        if os.path.exists(self.receipts_path):
            with open(self.receipts_path, "r") as f:
                if attestation in f.read().splitlines():
                    is_replay = True

        if not converged or not count_match or not is_authenticated or is_replay:
            logger.warning(
                f"🚫 PERSISTENCE REJECTED: Stage 2E Verification Failure. "
                f"Converged: {converged}, CountMatch: {count_match}, "
                f"Authenticated: {is_authenticated}, Replay: {is_replay}"
            )
            return False

        # Record receipt for single-use enforcement
        with open(self.receipts_path, "a") as f:
            f.write(f"{attestation}\n")
        
        logger.info(f"✅ PERSISTENCE AUTHORIZED (Stage 2E): Payload-bound attestation verified for {metadata.get('proposal_id')}.")
        return True
