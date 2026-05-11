from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import csv
import os
import math
import hashlib

@dataclass
class IzhikevichNeuronConfig:
    id: str
    a: float
    b: float
    c: float
    d: float
    v0: float
    u0: float
    threshold_mV: float = 30.0

@dataclass
class ConnectionConfig:
    source_id: str
    target_id: str
    weight: float

@dataclass
class NetworkParameters:
    neurons: List[IzhikevichNeuronConfig]
    connections: List[ConnectionConfig]
    dt_ms: float = 1.0
    duration_ms: float = 300.0
    input_schedules: Dict[str, List[Dict[str, float]]] = field(default_factory=dict)

    def to_dict(self):
        return {
            "neurons": [vars(n) for n in self.neurons],
            "connections": [vars(c) for c in self.connections],
            "dt_ms": self.dt_ms,
            "duration_ms": self.duration_ms,
            "input_schedules": self.input_schedules
        }

def simulate_network(params: NetworkParameters):
    dt = params.dt_ms
    n_steps = int(params.duration_ms / dt)
    
    # Initialize state
    states = {}
    for n in params.neurons:
        states[n.id] = {'v': n.v0, 'u': n.u0, 'spiked': False}
    
    # Map connections for faster lookup
    adj = {n.id: [] for n in params.neurons}
    for c in params.connections:
        adj[c.source_id].append((c.target_id, c.weight))
    
    history = []
    spike_counts = {n.id: 0 for n in params.neurons}

    for i in range(n_steps):
        t = i * dt
        step_data = {'t_ms': t, 'neurons': {}}
        
        # 1. Determine external input and synaptic input
        inputs = {n.id: 0.0 for n in params.neurons}
        
        # External input
        for nid, schedule in params.input_schedules.items():
            for entry in schedule:
                if entry['start_ms'] <= t < entry['end_ms']:
                    inputs[nid] += entry['I']
                    break
        
        # Synaptic input from spikes in PREVIOUS step
        # (Simple implementation: if source spiked last step, add weight to input this step)
        for nid, state in states.items():
            if state['spiked']:
                for target_id, weight in adj[nid]:
                    inputs[target_id] += weight

        # 2. Update neurons
        for n in params.neurons:
            nid = n.id
            v = states[nid]['v']
            u = states[nid]['u']
            I = inputs[nid]
            
            # Check for spike
            if v >= n.threshold_mV:
                spike_counts[nid] += 1
                states[nid]['spiked'] = True
                states[nid]['v'] = n.c
                states[nid]['u'] = u + n.d
            else:
                states[nid]['spiked'] = False
                dv = (0.04 * v**2 + 5 * v + 140 - u + I) * dt
                du = (n.a * (n.b * v - u)) * dt
                states[nid]['v'] += dv
                states[nid]['u'] += du
            
            step_data['neurons'][nid] = {
                'v_mV': states[nid]['v'],
                'u': states[nid]['u'],
                'I_ext': inputs[nid] # Includes synaptic input in this simplified view
            }
            
        history.append(step_data)

    return history, spike_counts

def calculate_network_metrics(history, params: NetworkParameters, spike_counts):
    # Flatten history for global max/min if needed
    metrics = {
        "n_time_steps": len(history),
        "spike_counts": spike_counts,
        "neuron_metrics": {}
    }
    
    for n in params.neurons:
        nid = n.id
        v_trace = [step['neurons'][nid]['v_mV'] for step in history]
        metrics["neuron_metrics"][nid] = {
            "max_v_pre_reset_mV": max(v_trace),
            "min_v_mV": min(v_trace),
            "spike_count": spike_counts[nid]
        }
    
    metrics["voltage_recording_convention"] = "pre_reset_overshoot_recorded"
    return metrics

def write_network_artifacts(run_dir, params: NetworkParameters, history, metrics):
    os.makedirs(run_dir, exist_ok=True)
    
    with open(os.path.join(run_dir, "network_parameters.json"), "w") as f:
        json.dump(params.to_dict(), f, indent=2)

    # Simplified trace writing: one CSV per neuron or a wide CSV
    # Let's do a wide CSV: t, v_n1, u_n1, I_n1, v_n2, u_n2, I_n2...
    fieldnames = ['t_ms']
    for n in params.neurons:
        fieldnames.extend([f'v_{n.id}', f'u_{n.id}', f'I_{n.id}'])
    
    trace_path = os.path.join(run_dir, "network_trace.csv")
    with open(trace_path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for step in history:
            row = {'t_ms': step['t_ms']}
            for nid, data in step['neurons'].items():
                row[f'v_{nid}'] = data['v_mV']
                row[f'u_{nid}'] = data['u']
                row[f'I_{nid}'] = data['I_ext']
            writer.writerow(row)

    with open(os.path.join(run_dir, "network_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # Receipt Candidate
    receipt = {
        "phase": "izhikevich_network_validation",
        "truth_mode": "truth_safe_unverified",
        "truth_bearing_run": False,
        "claim_type": "simulation_result",
        "model_scope": "network_component_growth",
        "biological_truth_claim": False,
        "growth_event": True,
        "previous_N": 1,
        "proposed_N": len(params.neurons),
        "metrics": metrics
    }
    with open(os.path.join(run_dir, "receipt_candidate.json"), "w") as f:
        json.dump(receipt, f, indent=2)

    # Manifest and Hashes
    artifact_files = [
        "network_parameters.json",
        "network_trace.csv",
        "network_metrics.json",
        "receipt_candidate.json"
    ]
    manifest = {
        "name": "izhikevich_network_validation",
        "artifacts": [{"file": f} for f in artifact_files]
    }
    with open(os.path.join(run_dir, "artifact_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    hash_lines = []
    for f_name in artifact_files + ["artifact_manifest.json"]:
        f_path = os.path.join(run_dir, f_name)
        with open(f_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
            hash_lines.append(f"{h}  {f_name}")
    
    with open(os.path.join(run_dir, "hashes.sha256"), "w") as f:
        f.write("\n".join(hash_lines) + "\n")
