import pytest
import os
import shutil
import json
from gamma_runtime.science_components.izhikevich_network import (
    IzhikevichNeuronConfig,
    ConnectionConfig,
    NetworkParameters,
    simulate_network,
    calculate_network_metrics,
    write_network_artifacts
)

def test_ei_pair_simulation_logic():
    # Define E neuron (Seed N1 parameters)
    n1 = IzhikevichNeuronConfig(
        id="N1", a=0.02, b=0.2, c=-65.0, d=8.0, v0=-65.0, u0=-13.0
    )
    # Define I neuron (FS parameters)
    n2 = IzhikevichNeuronConfig(
        id="N2", a=0.1, b=0.2, c=-65.0, d=2.0, v0=-65.0, u0=-13.0
    )
    
    # Reciprocal connectivity
    connections = [
        ConnectionConfig(source_id="N1", target_id="N2", weight=100.0), # Extremely Strong E->I
        ConnectionConfig(source_id="N2", target_id="N1", weight=-10.0) # Strong I->E
    ]
    
    # Input to N1 only
    input_schedules = {
        "N1": [{"start_ms": 100.0, "end_ms": 250.0, "I": 10.0}]
    }
    
    params = NetworkParameters(
        neurons=[n1, n2],
        connections=connections,
        input_schedules=input_schedules,
        duration_ms=300.0
    )
    
    history, spike_counts = simulate_network(params)
    metrics = calculate_network_metrics(history, params, spike_counts)
    
    assert len(history) == 300
    assert "N1" in spike_counts
    assert "N2" in spike_counts
    
    # N1 should spike because of input
    assert spike_counts["N1"] > 0
    # N2 should spike because of N1 activity
    assert spike_counts["N2"] > 0

def test_network_artifact_generation(tmp_path):
    n1 = IzhikevichNeuronConfig(id="N1", a=0.02, b=0.2, c=-65.0, d=8.0, v0=-65.0, u0=-13.0)
    params = NetworkParameters(neurons=[n1], connections=[], duration_ms=10.0)
    
    history, spike_counts = simulate_network(params)
    metrics = calculate_network_metrics(history, params, spike_counts)
    
    run_dir = tmp_path / "test_run"
    write_network_artifacts(str(run_dir), params, history, metrics)
    
    assert (run_dir / "artifact_manifest.json").exists()
    assert (run_dir / "hashes.sha256").exists()
    assert (run_dir / "receipt_candidate.json").exists()
    
    with open(run_dir / "receipt_candidate.json", "r") as f:
        receipt = json.load(f)
        assert receipt["proposed_N"] == 1
        assert receipt["growth_event"] is True
