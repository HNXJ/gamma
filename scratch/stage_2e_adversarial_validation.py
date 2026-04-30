import os
import sys
import json
import logging

# Add src to path
sys.path.append(os.getcwd())

from src.sde_engine.adapter import ExecutionAdapter
from src.gamma_runtime.types import MissionContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Stage2E-Validator")

def run_adversarial_suite():
    proposals_dir = "local/game001/proposals"
    os.makedirs(proposals_dir, exist_ok=True)
    
    # Initialize Adapter
    adapter = ExecutionAdapter(proposals_dir)
    mission = MissionContext(target_neuron_count=11, mission_topic="Continuous Growth: 10 to 11", patch_id="p123")
    
    # Create a dummy proposal
    proposal_id = "test_prop_001"
    proposal_data = {
        "meta": {"neuron_count": 11},
        "params": {"voltage_threshold": -50, "dt": 0.1}
    }
    with open(os.path.join(proposals_dir, f"{proposal_id}.json"), "w") as f:
        json.dump(proposal_data, f)

    results = []

    # --- TEST 1: Authentic Path ---
    logger.info("Test 1: Running authentic materialization and verification...")
    config = adapter.materialize_proposal(proposal_id, mission)
    # Simulate solver output
    metadata = {
        "status": "converged",
        "converged": True,
        "neuron_count": 11,
        "proposal_id": proposal_id,
        "mission_topic": mission.mission_topic,
        "provenance": config["provenance"]
    }
    success = adapter.verify_substrate_success(metadata, 11)
    results.append(("Authentic Path", success))

    # --- TEST 2: Forged Signature ---
    logger.info("Test 2: Testing forged signature...")
    forged_metadata = json.loads(json.dumps(metadata))
    forged_metadata["provenance"]["attestation"] = "a" * 64
    success = adapter.verify_substrate_success(forged_metadata, 11)
    results.append(("Forged Signature Fails", not success))

    # --- TEST 3: Altered target_count ---
    logger.info("Test 3: Testing altered target_count...")
    altered_n_metadata = json.loads(json.dumps(metadata))
    altered_n_metadata["neuron_count"] = 12
    success = adapter.verify_substrate_success(altered_n_metadata, 11)
    results.append(("Altered target_count Fails", not success))

    # --- TEST 4: Altered config payload (Payload Swapping) ---
    logger.info("Test 4: Testing altered config payload (config_hash mismatch)...")
    altered_payload_metadata = json.loads(json.dumps(metadata))
    altered_payload_metadata["provenance"]["config_hash"] = "f" * 64
    success = adapter.verify_substrate_success(altered_payload_metadata, 11)
    results.append(("Altered config_hash Fails", not success))

    # --- TEST 5: Canonicalization Equivalence ---
    logger.info("Test 5: Testing canonicalization equivalence...")
    # Materialize two configs that are semantically identical but different key order
    h1 = adapter._canonical_hash({"a": 1, "b": 2})
    h2 = adapter._canonical_hash({"b": 2, "a": 1})
    results.append(("Canonical Hashing (Order-Independent)", h1 == h2))

    # --- TEST 6: Replay after commit ---
    logger.info("Test 6: Testing replay after commit...")
    # The first authentic run already committed a receipt.
    success = adapter.verify_substrate_success(metadata, 11)
    results.append(("Replay Fails", not success))

    # --- TEST 7: Restart resilience ---
    logger.info("Test 7: Testing restart resilience...")
    # We need a NEW attestation so it's not in the receipt log
    proposal_id_3 = "test_prop_003"
    with open(os.path.join(proposals_dir, f"{proposal_id_3}.json"), "w") as f:
        json.dump(proposal_data, f)
    config_3 = adapter.materialize_proposal(proposal_id_3, mission)
    
    # Use a fresh adapter instance with no memory of run_ids
    adapter_new = ExecutionAdapter(proposals_dir)
    metadata_3 = {
        "status": "converged", "converged": True, "neuron_count": 11,
        "proposal_id": proposal_id_3, "mission_topic": mission.mission_topic,
        "provenance": config_3["provenance"]
    }
    success = adapter_new.verify_substrate_success(metadata_3, 11)
    # NOTE: If we want true restart resilience, we must remove 'is_registered' check from adapter.py
    # or make the registry persistent. 
    results.append(("Restart Resilience", success))

    # --- TEST 8: Cross-Mission Reuse ---
    logger.info("Test 8: Testing reused attestation under different mission...")
    # Generate one for mission A, try to use for mission B
    config_4 = adapter.materialize_proposal(proposal_id_3, mission)
    bad_mission_metadata = {
        "status": "converged", "converged": True, "neuron_count": 11,
        "proposal_id": proposal_id_3, "mission_topic": "Different Mission",
        "provenance": config_4["provenance"]
    }
    # provenance.mission_id is what's signed.
    bad_mission_metadata["provenance"]["mission_id"] = "Malicious Mission"
    success = adapter.verify_substrate_success(bad_mission_metadata, 11)
    results.append(("Cross-Mission Reuse Fails", not success))

    print("\n--- ADVERSARIAL VALIDATION SUMMARY ---")
    for test, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {test}")

if __name__ == "__main__":
    run_adversarial_suite()
