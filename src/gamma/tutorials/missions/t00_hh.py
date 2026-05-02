import os
import sys
import time
import numpy as np
from typing import Dict, Any
from gamma.tutorials.harness import TutorialHarness

class T00SingleNeuronHH(TutorialHarness):
    """
    T00: Single-Neuron Hodgkin-Huxley Simulation.
    Validates basic biophysical integration and artifact generation.
    """
    def __init__(self, root_dir: str):
        super().__init__(root_dir, "T00_single_neuron_hh")
        self.jbiophysic_src = os.path.join(root_dir, "src/computational/jbiophysic/src")
        if self.jbiophysic_src not in sys.path:
            sys.path.append(self.jbiophysic_src)

    async def execute(self):
        try:
            # 0. Apply compatibility shim from Gamma side
            from gamma.tutorials.compatibility import apply_jaxley_monkeypatch
            apply_jaxley_monkeypatch()
            
            import jaxley as jx
            from jaxley.channels import HH
            
            # 1. Setup Mission Config
            config = {
                "t_max": 500.0,
                "dt": 0.1,
                "seed": 42
            }
            self.write_artifact("mission_config.json", config)
            self.generate_run_manifest("RUNNING", config)
            
            # 2. Build HH Single Neuron
            # We use jaxley directly to ensure compatibility with 0.13.0
            cell = jx.Cell([jx.Branch(ncomp=1)], parents=[-1])
            cell.insert(HH())
            
            # Record voltage
            cell.record("v")
            
            # Add stimulus
            # Jaxley 0.13.0 step_current
            current = jx.step_current(
                i_delay=10.0, 
                i_dur=480.0, 
                i_amp=0.1, 
                delta_t=config["dt"], 
                t_max=config["t_max"]
            )
            # Applying stimulus to the first compartment of the only branch
            cell.branch(0).comp(0).stimulate(current)
            
            # 3. Run Simulation
            # We bypass jbiophysic.models.simulation.run.run_simulation 
            # because it's broken for Jaxley 0.13.0 in the pinned commit.
            v_trace = jx.integrate(
                cell,
                t_max=config["t_max"],
                delta_t=config["dt"]
            )
            
            # 4. Process Results & Metrics
            v_trace = np.array(v_trace) # Result is (n_neurons, n_timesteps) 
            
            # Calculate simple spikes (threshold crossing at -20mV)
            threshold = -20.0
            spikes = (v_trace[:, :-1] < threshold) & (v_trace[:, 1:] >= threshold)
            spike_counts = np.sum(spikes, axis=1)
            
            metrics = {
                "run_id": self.run_id,
                "tutorial_id": self.tutorial_id,
                "source_commit": "fb6c8505c4b4c171cb5ede8de5c6c517f82d9ffa",
                "model_kind": "HH",
                "n_neurons": 1,
                "duration_ms": config["t_max"],
                "dt_ms": config["dt"],
                "spike_count_mean": float(np.mean(spike_counts)),
                "spike_count_variance": float(np.var(spike_counts)),
                "firing_rate_hz_mean": float(np.mean(spike_counts) / (config["t_max"] / 1000.0)),
                "firing_rate_hz_variance": 0.0, # only one neuron
                "voltage_mean": float(np.mean(v_trace)),
                "voltage_variance": float(np.var(v_trace)),
                "parameter_mean": {},
                "parameter_variance": {},
                "warnings": ["Submodule run_simulation bypassed due to 0.13.0 incompatibility"],
                "artifact_paths": {
                    "v_trace": "v_trace.npy",
                    "metrics": "summary_metrics.json"
                },
                "evaluation_decision": "PENDING",
                "promotion_eligible": False
            }
            
            # Save artifacts
            np.save(os.path.join(self.artifact_dir, "v_trace.npy"), v_trace)
            
            # 5. Evaluate
            decision = "PASS"
            notes = "Simulation completed successfully using Gamma-side harness."
            
            if v_trace.size == 0:
                decision = "FAIL"
                notes = "Voltage trace is empty."
            
            metrics["evaluation_decision"] = decision
            self.write_artifact("summary_metrics.json", metrics)
            self.generate_evaluation(decision, notes)
            self.generate_run_manifest("COMPLETED", config)
            
            return metrics

        except Exception as e:
            import traceback
            error_msg = f"T00 Execution failed: {str(e)}\n{traceback.format_exc()}"
            self.write_artifact("error.log", error_msg)
            self.generate_run_manifest("FAILED", {})
            raise
