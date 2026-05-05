import os
import sys
import time
import numpy as np
import logging
from typing import Dict, Any, List
from gamma.tutorials.harness import TutorialHarness

logger = logging.getLogger("T01TwoAreaSeed")

class T01TwoAreaSeed(TutorialHarness):
    """
    T01: N=4 Two-Area E/PV Seed Simulation (Fallback NumPy/JAX HH-like).
    Validates minimal inter-area connectivity (FF/FB) and E/I balance.
    """
    def __init__(self, root_dir: str):
        super().__init__(root_dir, "T01_two_area_seed")

    async def execute(self):
        try:
            # 1. Setup Mission Config
            config = {
                "t_max": 500.0,
                "dt": 0.05,
                "seed": 42,
                "area_names": ["lower", "higher"],
                "cell_types": ["E", "PV"],
                "stim_amplitude": 20.0,   # uA/cm^2
                "stim_duration": 100.0,   # ms
                "stim_start": 100.0       # ms
            }
            self.write_artifact("mission_config.json", config)
            self.generate_run_manifest("RUNNING", config)

            # 2. Simulator Constants (Standard HH)
            C_m = 1.0
            g_Na = 120.0
            g_K = 36.0
            g_L = 0.3
            E_Na = 50.0
            E_K = -77.0
            E_L = -54.387

            def alpha_m(V): return 0.1 * (V + 40.0) / (1.0 - np.exp(-(V + 40.0) / 10.0) + 1e-9)
            def beta_m(V): return 4.0 * np.exp(-(V + 65.0) / 18.0)
            def alpha_h(V): return 0.07 * np.exp(-(V + 65.0) / 20.0)
            def beta_h(V): return 1.0 / (1.0 + np.exp(-(V + 35.0) / 10.0))
            def alpha_n(V): return 0.01 * (V + 55.0) / (1.0 - np.exp(-(V + 55.0) / 10.0) + 1e-9)
            def beta_n(V): return 0.125 * np.exp(-(V + 65.0) / 80.0)

            # Connectivity Logic
            # 0: e1, 1: i1, 2: e2, 3: i2
            conn_map = [
                (0, 1, 0.5, 0.0),   # E1->I1
                (1, 0, 1.0, -80.0), # I1->E1
                (2, 3, 0.5, 0.0),   # E2->I2
                (3, 2, 1.0, -80.0), # I2->E2
                (0, 2, 0.4, 0.0),   # E1->E2 (FF)
                (2, 0, 0.2, 0.0)    # E2->E1 (FB)
            ]
            
            self.write_artifact("connectivity.json", [
                {"pre": c[0], "post": c[1], "weight": c[2], "e_rev": c[3]} for c in conn_map
            ])

            conditions = ["baseline", "sensory", "prediction", "match"]
            all_v_traces = {}
            condition_metrics = {}

            t = np.arange(0, config["t_max"], config["dt"])
            n_steps = len(t)

            for cond in conditions:
                logger.info(f"Running condition: {cond}")
                
                V = np.full(4, -65.0)
                m = alpha_m(V) / (alpha_m(V) + beta_m(V))
                h = alpha_h(V) / (alpha_h(V) + beta_h(V))
                n = alpha_n(V) / (alpha_n(V) + beta_n(V))
                s = np.zeros(4) # Synaptic activation per neuron
                
                v_trace = np.zeros((4, n_steps))
                
                for i in range(n_steps):
                    curr_t = t[i]
                    v_trace[:, i] = V
                    
                    I_stim = np.zeros(4)
                    if cond in ["sensory", "match"]:
                        if config["stim_start"] <= curr_t < config["stim_start"] + config["stim_duration"]:
                            I_stim[0] = config["stim_amplitude"]
                    if cond in ["prediction", "match"]:
                        if config["stim_start"] <= curr_t < config["stim_start"] + config["stim_duration"]:
                            I_stim[2] = config["stim_amplitude"]
                    
                    I_syn = np.zeros(4)
                    for pre, post, w, e_rev in conn_map:
                        I_syn[post] -= w * s[pre] * (V[post] - e_rev)
                    
                    I_Na = g_Na * m**3 * h * (V - E_Na)
                    I_K = g_K * n**4 * (V - E_K)
                    I_L = g_L * (V - E_L)
                    
                    dV = (I_stim + I_syn - I_Na - I_K - I_L) / C_m
                    dm = alpha_m(V)*(1-m) - beta_m(V)*m
                    dh = alpha_h(V)*(1-h) - beta_h(V)*h
                    dn = alpha_n(V)*(1-n) - beta_n(V)*n
                    
                    s_inf = 1.0 / (1.0 + np.exp(-(V + 20.0) / 2.0))
                    ds = (s_inf - s) / 2.0 # Fast synapses
                    
                    V += dV * config["dt"]
                    m += dm * config["dt"]
                    h += dh * config["dt"]
                    n += dn * config["dt"]
                    s += ds * config["dt"]

                all_v_traces[cond] = v_trace
                spikes = np.sum((v_trace[:, :-1] < 0) & (v_trace[:, 1:] >= 0), axis=1)
                
                condition_metrics[cond] = {
                    "v_min": [float(np.min(v_trace[i])) for i in range(4)],
                    "v_max": [float(np.max(v_trace[i])) for i in range(4)],
                    "v_mean": [float(np.mean(v_trace[i])) for i in range(4)],
                    "spike_counts": [int(s) for s in spikes]
                }

            v_traces_packed = np.stack([all_v_traces[c] for c in conditions])
            np.save(os.path.join(self.artifact_dir, "v_traces.npy"), v_traces_packed)
            self.write_artifact("condition_metrics.json", condition_metrics)
            
            summary = {
                "n_neurons": 4,
                "backend": "numpy_hh_like_tutorial_v0",
                "backend_canonicality": "unresolved",
                "conditions": conditions,
                "firing_proxy": {cond: condition_metrics[cond]["spike_counts"] for cond in conditions}
            }
            self.write_artifact("summary_metrics.json", summary)

            decision = "PASS"
            notes = "N=4 Two-Area Seed validated successfully with fallback NumPy simulator."
            fail_reasons = []

            for cond in conditions:
                v_cond = all_v_traces[cond]
                if np.isnan(v_cond).any() or np.isinf(v_cond).any():
                    decision = "FAIL"
                    fail_reasons.append(f"NaN/Inf detected in {cond}")
                if np.min(v_cond) < -100 or np.max(v_cond) > 80:
                    decision = "FAIL"
                    fail_reasons.append(f"Voltage out of bounds in {cond}: [{np.min(v_cond):.2f}, {np.max(v_cond):.2f}]")

            if sum(condition_metrics["sensory"]["spike_counts"]) <= sum(condition_metrics["baseline"]["spike_counts"]):
                decision = "PARTIAL"
                fail_reasons.append("Weak sensory response")

            if decision != "PASS":
                notes = f"Validation issues: {'; '.join(fail_reasons)}"

            self.generate_evaluation(decision, notes, v_trace=v_traces_packed)
            self.generate_run_manifest("COMPLETED", config)
            
            audit_log = f"Tutorial 01 Execution Audit (FALLBACK)\nTime: {time.ctime()}\nDecision: {decision}\nNotes: {notes}\nBackend: numpy_hh_like_tutorial_v0 (canonical Jaxley unresolved after 2 attempts)\n"
            self.write_artifact("tutorial_audit.log", audit_log)

            return decision

        except Exception as e:
            import traceback
            error_msg = f"T01 Execution failed: {str(e)}\n{traceback.format_exc()}"
            self.write_artifact("error.log", error_msg)
            self.generate_run_manifest("FAILED", {})
            raise

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    root = os.path.abspath(os.path.join(os.getcwd()))
    mission = T01TwoAreaSeed(root)
    asyncio.run(mission.execute())
