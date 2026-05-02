import os
import sys
import time
import numpy as np
from typing import Dict, Any
from gamma.tutorials.harness import TutorialHarness

class T01TwoNeuronEI(TutorialHarness):
    """
    T01: Two-Neuron E/I Network Simulation.
    Validates synaptic connectivity and network-level artifact generation.
    """
    def __init__(self, root_dir: str):
        super().__init__(root_dir, "T01_two_neuron_ei")

    async def execute(self):
        try:
            from gamma.tutorials.compatibility import apply_jaxley_monkeypatch
            apply_jaxley_monkeypatch()
            
            import jaxley as jx
            from jaxley.channels import HH
            from jaxley.synapses import IonotropicSynapse
            
            # 1. Setup Mission Config
            config = {
                "t_max": 500.0,
                "dt": 0.1,
                "seed": 42
            }
            self.write_artifact("mission_config.json", config)
            self.generate_run_manifest("RUNNING", config)
            
            # 2. Build 2-Neuron Network (Excitatory + Inhibitory)
            # Create two identical cells
            exc_cell = jx.Cell([jx.Branch(ncomp=1)], parents=[-1])
            inh_cell = jx.Cell([jx.Branch(ncomp=1)], parents=[-1])
            
            # Insert HH channels
            exc_cell.insert(HH())
            inh_cell.insert(HH())
            
            # Combine into a network/set
            net = jx.Network([exc_cell, inh_cell])
            
            # Define Synapses
            # Exc -> Inh (Excitatory)
            # Inh -> Exc (Inhibitory)
            # jaxley.synapses.IonotropicSynapse
            
            # Connect Exc (0) to Inh (1)
            net.connect(net.cell(0), net.cell(1), IonotropicSynapse())
            # Connect Inh (1) to Exc (0)
            net.connect(net.cell(1), net.cell(0), IonotropicSynapse())
            
            # Set synaptic parameters (reversal potentials)
            # g_max, e_rev
            # Cell 0 -> Cell 1 (Excitatory: e_rev = 0.0)
            # Cell 1 -> Cell 0 (Inhibitory: e_rev = -80.0)
            net.synapse(0).set("e_rev", 0.0)
            net.synapse(1).set("e_rev", -80.0)
            
            # 3. Stimulation & Recording
            net.record("v")
            
            # Stimulate excitatory cell to drive the network
            current = jx.step_current(
                i_delay=10.0, 
                i_dur=480.0, 
                i_amp=0.2, 
                delta_t=config["dt"],
                t_max=config["t_max"]
            )
            net.cell(0).branch(0).comp(0).stimulate(current)
            
            # 4. Run Simulation
            v_traces = jx.integrate(
                net,
                t_max=config["t_max"],
                delta_t=config["dt"]
            )
            
            # 5. Process Results
            v_traces = np.array(v_traces) # (2, n_timesteps)
            
            threshold = -20.0
            spikes = (v_traces[:, :-1] < threshold) & (v_traces[:, 1:] >= threshold)
            spike_counts = np.sum(spikes, axis=1)
            
            metrics = {
                "run_id": self.run_id,
                "tutorial_id": self.tutorial_id,
                "source_commit": "fb6c8505c4b4c171cb5ede8de5c6c517f82d9ffa",
                "model_kind": "HH_EI_PAIR",
                "n_neurons": 2,
                "duration_ms": config["t_max"],
                "dt_ms": config["dt"],
                "spike_count_mean": float(np.mean(spike_counts)),
                "spike_count_variance": float(np.var(spike_counts)),
                "firing_rate_hz_mean": float(np.mean(spike_counts) / (config["t_max"] / 1000.0)),
                "firing_rate_hz_variance": float(np.var(spike_counts) / (config["t_max"] / 1000.0)),
                "voltage_mean": float(np.mean(v_traces)),
                "voltage_variance": float(np.var(v_traces)),
                "parameter_mean": {
                    "e_rev_exc": 0.0,
                    "e_rev_inh": -80.0
                },
                "parameter_variance": {},
                "warnings": [],
                "artifact_paths": {
                    "v_traces": "v_traces.npy",
                    "metrics": "summary_metrics.json"
                },
                "evaluation_decision": "PENDING",
                "promotion_eligible": False
            }
            
            # Save artifacts
            np.save(os.path.join(self.artifact_dir, "v_traces.npy"), v_traces)
            
            # 6. Evaluate
            decision = "PASS"
            notes = "E/I network simulation completed successfully."
            
            if v_traces.shape[0] != 2:
                decision = "FAIL"
                notes = f"Expected 2 neurons, got {v_traces.shape[0]}"
            elif np.any(np.isnan(v_traces)):
                decision = "FAIL"
                notes = "NaN detected in voltage traces."
            
            metrics["evaluation_decision"] = decision
            self.write_artifact("summary_metrics.json", metrics)
            self.generate_evaluation(decision, notes)
            self.generate_run_manifest("COMPLETED", config)
            
            return metrics

        except Exception as e:
            import traceback
            error_msg = f"T01 Execution failed: {str(e)}\n{traceback.format_exc()}"
            self.write_artifact("error.log", error_msg)
            self.generate_run_manifest("FAILED", {})
            raise
