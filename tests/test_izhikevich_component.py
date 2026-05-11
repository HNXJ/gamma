import pytest
import os
import json
import shutil
from gamma_runtime.science_components.izhikevich_component import (
    IzhikevichParameters,
    simulate_izhikevich,
    calculate_metrics,
    write_artifacts
)

def test_izhikevich_deterministic():
    params = IzhikevichParameters()
    trace1, sc1, fsm1 = simulate_izhikevich(params)
    trace2, sc2, fsm2 = simulate_izhikevich(params)
    
    assert sc1 == sc2
    assert fsm1 == fsm2
    assert len(trace1) == len(trace2)
    for r1, r2 in zip(trace1, trace2):
        assert r1['v_mV'] == r2['v_mV']
        assert r1['u'] == r2['u']

def test_izhikevich_metrics_parity():
    # Expected values from N=1 seed candidate
    # spike_count: 4
    # max_v_pre_reset_mV: 369.1513238980028
    
    params = IzhikevichParameters()
    trace, sc, fsm = simulate_izhikevich(params)
    metrics = calculate_metrics(trace, params, sc, fsm)
    
    assert metrics['spike_count'] == 4
    assert pytest.approx(metrics['max_v_pre_reset_mV']) == 369.1513238980028
    assert metrics['max_v_clipped_mV'] == 30.0
    assert metrics['threshold_mV'] == 30.0
    assert metrics['nan_count'] == 0
    assert metrics['inf_count'] == 0
    assert metrics['voltage_recording_convention'] == "pre_reset_overshoot_recorded"

def test_izhikevich_artifact_generation(tmp_path):
    run_dir = tmp_path / "test_run"
    params = IzhikevichParameters()
    trace, sc, fsm = simulate_izhikevich(params)
    metrics = calculate_metrics(trace, params, sc, fsm)
    
    write_artifacts(str(run_dir), params, trace, metrics, study_question="Test question")
    
    assert (run_dir / "artifact_manifest.json").exists()
    assert (run_dir / "hashes.sha256").exists()
    assert (run_dir / "receipt_candidate.json").exists()
    assert (run_dir / "simulation_metrics.json").exists()
    assert (run_dir / "simulation_trace.csv").exists()
    assert (run_dir / "izhikevich_parameters.json").exists()
    assert (run_dir / "study_question.json").exists()

    with open(run_dir / "receipt_candidate.json", "r") as f:
        receipt = json.load(f)
        assert receipt['truth_mode'] == "truth_safe_unverified"
        assert receipt['truth_bearing_run'] is False
        assert receipt['model_scope'] == "single_component_only"
        assert receipt['biological_truth_claim'] is False
        assert receipt['growth_event'] is False
        assert receipt['omission_claim'] is False
        assert receipt['voltage_sanity_interpretation'] == "finite_numerical_sanity_only_not_biophysical_voltage_claim"

def test_izhikevich_replay_integrity(tmp_path):
    run_dir = tmp_path / "replay_run"
    params = IzhikevichParameters()
    trace, sc, fsm = simulate_izhikevich(params)
    metrics = calculate_metrics(trace, params, sc, fsm)
    
    write_artifacts(str(run_dir), params, trace, metrics)
    
    # Re-read parameters and simulate again
    with open(run_dir / "izhikevich_parameters.json", "r") as f:
        params_dict = json.load(f)
        params_reloaded = IzhikevichParameters(**params_dict)
    
    trace_r, sc_r, fsm_r = simulate_izhikevich(params_reloaded)
    metrics_r = calculate_metrics(trace_r, params_reloaded, sc_r, fsm_r)
    
    assert metrics_r['spike_count'] == metrics['spike_count']
    assert metrics_r['max_v_pre_reset_mV'] == metrics['max_v_pre_reset_mV']
    assert metrics_r['reproducible_replay_pass'] is True
