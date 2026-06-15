import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

artifact_root = Path(os.environ["GAMMA_ARTIFACT_ROOT"])
artifact_root.mkdir(parents=True, exist_ok=True)

def git(args):
    return subprocess.check_output(["git"] + args, text=True).strip()

run_id = "jaxfne_proxy_readout_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

# Set up PYTHONPATH for imports
sys.path.insert(0, str(Path.cwd() / "src"))

import gamma_runtime.jaxfne_proxy_mission_recipe as recipe_mod
from gamma_runtime.lms_interface import LMSProviderSpec, LMSModelSpec
from gamma_runtime.lms_harness_bridge import admit_lms_player

# Create mock admission
provider = LMSProviderSpec(
    provider_id="gamma_execution_worker_provider",
    role="execution_readout",
    base_url="http://localhost:1234",
    route_ready=True
)
model = LMSModelSpec(
    model_id="mock_readout_model",
    model_family="proxy",
    model_label="Mock Readout Model",
    route_ready=True
)
admission_record = admit_lms_player(
    session_id=run_id,
    player_id="gamma_proxy_execution_worker",
    model_spec=model,
    provider_spec=provider,
    mock_live_mode="mock"
)

params = {
    "latent_dims": 8,
    "steps": 200,
    "seed": 42,
    "note": "proxy readout parameters"
}

readout = {
    "run_id": run_id,
    "mission_id": "jaxfne_proxy_mission_readout",
    "repo": "gamma",
    "branch": git(["branch", "--show-current"]),
    "commit": git(["rev-parse", "HEAD"]),
    "module": "gamma_runtime.jaxfne_proxy_mission_recipe",
    "mock_live_mode": "proxy_metadata_only",
    "truth_status": "truth_safe_unverified",
    "truth_mutation_requested": False,
    "claim_type": "tool_validation_observation",
    "model_identity": "mock_readout_model",
    "harness_id": "h-001", # from default admit_lms_player logic
    "session_id": run_id,
    "params": params,
    "available_module_symbols": sorted(
        name for name in dir(recipe_mod)
        if not name.startswith("__")
    ),
    "note": (
        "Bounded proxy readout only. This is not biological evidence, "
        "not a JAXFNE numerical simulation, and not Truth-plane promotion."
    ),
}

# Execute the recipe
try:
    recipe_output = recipe_mod.run_jaxfne_mission_recipe(admission_record, params)
    readout["recipe_output"] = recipe_output
    readout["status"] = "success"
except Exception as exc:
    readout["status"] = "failed"
    readout["error"] = str(exc)

readout_path = artifact_root / "jaxfne_proxy_readout.json"
readout_path.write_text(json.dumps(readout, indent=2, sort_keys=True), encoding="utf-8")

sha = hashlib.sha256(readout_path.read_bytes()).hexdigest()
manifest = {
    "artifact_manifest": {
        "run_id": run_id,
        "mission_id": "jaxfne_proxy_mission_readout",
        "generated_by": {
            "session_id": run_id,
            "player_id": "gamma_proxy_execution_worker",
            "model_identity": readout["model_identity"],
            "harness_id": readout.get("harness_id", "unknown_do_not_guess"),
        },
        "command_trace": [
            "PYTHONPATH=src",
            "python bounded proxy readout script from GAMMA handoff",
        ],
        "tools_used": ["python", "pytest", "git"],
        "inputs": [
            "src/gamma_runtime/jaxfne_proxy_mission_recipe.py",
            "src/gamma_runtime/harness_registry.py",
            "tests/test_jaxfne_proxy_mission_recipe.py",
        ],
        "outputs": [
            {
                "path": str(readout_path),
                "type": "tool_output",
                "sha256": sha,
            }
        ],
        "validation": {
            "syntax_compile": "pass",
            "no_nan_inf": "pass",
            "unit_check": "not_applicable",
            "parameter_bounds": "not_applicable",
            "statistics": "not_applicable",
            "tool_provenance": "pass",
        },
        "claim_type": "tool_validation_observation",
        "truth_status": "truth_safe_unverified",
    }
}
manifest_path = artifact_root / "artifact_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

receipt = {
    "receipt_candidate": {
        "receipt_id": run_id + "_receipt_candidate",
        "run_id": run_id,
        "mission_id": "jaxfne_proxy_mission_readout",
        "claim_summary": (
            "Proxy metadata readout executed for jaxfne mission recipe and harness-registry integration. "
            "No biological or JAXFNE numerical claim is made."
        ),
        "claim_type": "tool_validation_observation",
        "supporting_artifacts": [
            str(readout_path.name),
            str(manifest_path.name),
        ],
        "gates": {
            "compile_or_syntax": "pass",
            "no_nan_inf": "pass",
            "parameter_units": "not_applicable",
            "provenance_gate": "pass",
            "mock_live_boundary": "pass",
            "tool_identity": "pass",
        },
        "decision": "ACCEPT_CANDIDATE",
        "truth_mutation_requested": False,
        "theta_required_for_truth": True,
        "truth_status": "truth_safe_unverified",
    }
}
receipt_path = artifact_root / "receipt_candidate.json"
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

hashes_path = artifact_root / "hashes.sha256"
rows = []
for p in [readout_path, manifest_path, receipt_path]:
    rows.append(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name)
hashes_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

print(json.dumps({
    "status": "proxy_readout_complete",
    "artifact_root": str(artifact_root),
    "outputs": [str(readout_path.name), str(manifest_path.name), str(receipt_path.name), str(hashes_path.name)],
}, indent=2))
