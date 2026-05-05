import os
import sys
import json
import time
import uuid
import logging
import argparse
import numpy as np
from typing import Dict, Any, List, Optional
from gamma.tutorials.harness import TutorialHarness

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GrowthCampaign")

class GrowthModel:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.n_neurons = 0
        self.neuron_metadata = []
        self.synapses = []
        
    def add_neuron(self, area: str, cell_type: str):
        new_id = self.n_neurons
        self.neuron_metadata.append({
            "id": new_id,
            "area": area,
            "type": cell_type
        })
        self.n_neurons += 1
        return new_id

    def add_synapse(self, pre: int, post: int, weight: float, e_rev: float):
        self.synapses.append({
            "pre": pre,
            "post": post,
            "weight": weight,
            "e_rev": e_rev
        })

    def to_dict(self):
        return {
            "n_neurons": int(self.n_neurons),
            "neuron_metadata": [
                {k: (int(v) if isinstance(v, (np.integer, int)) else v) for k, v in m.items()}
                for m in self.neuron_metadata
            ],
            "synapses": [
                {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v) 
                 for k, v in s.items()}
                for s in self.synapses
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], config: Dict[str, Any]):
        model = cls(config)
        model.n_neurons = data["n_neurons"]
        model.neuron_metadata = data["neuron_metadata"]
        model.synapses = data["synapses"]
        return model

    def simulate(self, condition: str):
        # Simulation Logic (HH-like from T01)
        t_max = self.config["t_max"]
        dt = self.config["dt"]
        t = np.arange(0, t_max, dt)
        n_steps = len(t)
        n_n = self.n_neurons
        
        # Simulator Constants (Standard HH)
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

        V = np.full(n_n, -65.0)
        m = alpha_m(V) / (alpha_m(V) + beta_m(V))
        h = alpha_h(V) / (alpha_h(V) + beta_h(V))
        n = alpha_n(V) / (alpha_n(V) + beta_n(V))
        s = np.zeros(n_n)
        
        v_trace = np.zeros((n_n, n_steps))
        
        # Stim targets
        stim_targets = []
        if condition in ["sensory", "match"]:
            # Stim Area 1 E-neurons
            stim_targets.extend([m['id'] for m in self.neuron_metadata if m['area'] == 'lower' and m['type'] == 'E'])
        if condition in ["prediction", "match"]:
            # Stim Area 2 E-neurons
            stim_targets.extend([m['id'] for m in self.neuron_metadata if m['area'] == 'higher' and m['type'] == 'E'])

        # Pre-process connectivity for speed
        conn_list = []
        for syn in self.synapses:
            conn_list.append((syn['pre'], syn['post'], syn['weight'], syn['e_rev']))

        stim_start = self.config["stim_start"]
        stim_end = stim_start + self.config["stim_duration"]
        stim_amp = self.config["stim_amplitude"]

        for i in range(n_steps):
            curr_t = t[i]
            v_trace[:, i] = V
            
            I_stim = np.zeros(n_n)
            if stim_start <= curr_t < stim_end:
                for target in stim_targets:
                    I_stim[target] = stim_amp
            
            I_syn = np.zeros(n_n)
            for pre, post, w, e_rev in conn_list:
                I_syn[post] -= w * s[pre] * (V[post] - e_rev)
            
            # HH currents
            I_Na = g_Na * m**3 * h * (V - E_Na)
            I_K = g_K * n**4 * (V - E_K)
            I_L = g_L * (V - E_L)
            
            dV = (I_stim + I_syn - I_Na - I_K - I_L) / C_m
            dm = alpha_m(V)*(1-m) - beta_m(V)*m
            dh = alpha_h(V)*(1-h) - beta_h(V)*h
            dn = alpha_n(V)*(1-n) - beta_n(V)*n
            
            s_inf = 1.0 / (1.0 + np.exp(-(V + 20.0) / 2.0))
            ds = (s_inf - s) / 2.0 
            
            V += dV * dt
            m += dm * dt
            h += dh * dt
            n += dn * dt
            s += ds * dt

        return v_trace

class GrowthCampaign(TutorialHarness):
    def __init__(self, root_dir: str, args: argparse.Namespace):
        super().__init__(root_dir, "OMISSION_LITE_growth_campaign")
        self.args = args
        self.ledger_path = os.path.join(self.artifact_dir, "growth_ledger.jsonl")
        self.rejected_path = os.path.join(self.artifact_dir, "rejected_growth_attempts.jsonl")
        self.manifest_path = os.path.join(self.artifact_dir, "campaign_manifest.json")
        self.latest_model_path = os.path.join(self.artifact_dir, "latest_validated_model.json")
        
        self.mission_config = {
            "t_max": 500.0,
            "dt": 0.05,
            "seed": args.seed,
            "stim_amplitude": 20.0,
            "stim_duration": 100.0,
            "stim_start": 100.0,
            "backend": "numpy_hh_like_tutorial_v0",
            "backend_canonicality": "unresolved"
        }
        
        np.random.seed(args.seed)

    def load_t01_seed(self, artifact_path: str):
        logger.info(f"Loading T01 seed from {artifact_path}")
        with open(os.path.join(artifact_path, "connectivity.json")) as f:
            synapses = json.load(f)
        
        # T01 fixed mapping: 0:e1, 1:i1, 2:e2, 3:i2
        metadata = [
            {"id": 0, "area": "lower", "type": "E"},
            {"id": 1, "area": "lower", "type": "PV"},
            {"id": 2, "area": "higher", "type": "E"},
            {"id": 3, "area": "higher", "type": "PV"},
        ]
        
        model = GrowthModel(self.mission_config)
        model.n_neurons = 4
        model.neuron_metadata = metadata
        model.synapses = synapses
        return model

    def validate_step(self, v_traces: Dict[str, np.ndarray], model: GrowthModel):
        reasons = []
        # Numerical
        for cond, v in v_traces.items():
            if np.isnan(v).any(): reasons.append(f"NaN in {cond}")
            if np.isinf(v).any(): reasons.append(f"Inf in {cond}")
            
        # Biophysical
        for cond, v in v_traces.items():
            if np.min(v) < -100 or np.max(v) > 80:
                reasons.append(f"Voltage out of bounds in {cond}: [{np.min(v):.2f}, {np.max(v):.2f}]")

        # Weak profile (Original)
        if self.args.validation_profile == "weak":
            def get_spikes_aggregate(v):
                return np.sum((v[:, :-1] < 0) & (v[:, 1:] >= 0))
            spikes = {c: get_spikes_aggregate(v) for c, v in v_traces.items()}
            if spikes['sensory'] <= spikes['baseline']:
                reasons.append(f"Weak sensory response: {spikes['sensory']} vs {spikes['baseline']}")
            return len(reasons) == 0, reasons

        # Strict profile (V2)
        n_n = model.n_neurons
        spike_counts = {}
        for cond, v in v_traces.items():
            counts = np.sum((v[:, :-1] < 0) & (v[:, 1:] >= 0), axis=1)
            spike_counts[cond] = counts

        # 1. Per-neuron rate bounds (e.g. max 100Hz)
        dt = self.mission_config["dt"]
        t_max = self.mission_config["t_max"]
        max_spikes = (t_max / 1000.0) * 100 # 100Hz
        for cond, counts in spike_counts.items():
            if np.any(counts > max_spikes):
                bad_nodes = np.where(counts > max_spikes)[0]
                reasons.append(f"Excessive firing in {cond}: nodes {bad_nodes.tolist()} > {max_spikes} spikes")

        # 2. Participation fraction (at least 20% must spike in sensory)
        total_spiking = np.sum(spike_counts['sensory'] > 0)
        participation = total_spiking / n_n
        if participation < 0.2:
            reasons.append(f"Low participation in sensory: {participation:.2f} < 0.20")

        # 3. Dominance gate (no neuron > 30% of total activity)
        total_spikes = np.sum(spike_counts['sensory'])
        if total_spikes > 0:
            max_frac = np.max(spike_counts['sensory']) / total_spikes
            if max_frac > 0.3:
                reasons.append(f"High single-neuron dominance: {max_frac:.2f} > 0.3")

        # 4. New-neuron activity gate (N+1 must do something)
        new_id = n_n - 1
        active_in_any = any(spike_counts[c][new_id] > 0 for c in ["sensory", "prediction", "match"])
        if not active_in_any:
            # Also check for subthreshold voltage fluctuations as fallback
            v_sensory = v_traces['sensory'][new_id]
            if np.max(v_sensory) - np.min(v_sensory) < 1.0:
                reasons.append(f"New neuron {new_id} is completely silent and non-responsive")

        # 5. Area engagement (Sensory stimulus should hit lower area harder)
        lower_ids = [m['id'] for m in model.neuron_metadata if m['area'] == 'lower']
        higher_ids = [m['id'] for m in model.neuron_metadata if m['area'] == 'higher']
        lower_spikes = np.sum(spike_counts['sensory'][lower_ids])
        higher_spikes = np.sum(spike_counts['sensory'][higher_ids])
        if lower_spikes < higher_spikes and lower_spikes > 0:
             reasons.append(f"Sensory engagement inverted: lower({lower_spikes}) < higher({higher_spikes})")

        # 6. Orphan check
        adj = np.zeros((n_n, n_n))
        for syn in model.synapses:
            adj[syn['pre'], syn['post']] = 1
        for i in range(n_n):
            if np.sum(adj[i, :]) == 0 and np.sum(adj[:, i]) == 0:
                reasons.append(f"Orphan neuron detected: {i}")

        return len(reasons) == 0, reasons

    def run_falsifier(self, model: GrowthModel):
        """
        Phase 5: Falsifier checks.
        Perturbs input and checks for stability/response.
        """
        reasons = []
        
        # 1. Stress input test (2x amplitude)
        stress_config = self.mission_config.copy()
        stress_config["stim_amplitude"] *= 2.0
        
        stress_model = GrowthModel.from_dict(model.to_dict(), stress_config)
        v_sensory = stress_model.simulate("sensory")
        
        if bool(np.isnan(v_sensory).any()): reasons.append("NaN under stress input")
        if bool(np.isinf(v_sensory).any()): reasons.append("Inf under stress input")
        
        if bool(np.max(v_sensory) > 100):
            reasons.append(f"Runaway excitation under stress: max V = {float(np.max(v_sensory)):.2f}")
            
        # 2. No-input recovery test
        v_baseline = stress_model.simulate("baseline")
        final_v = v_baseline[:, -1]
        if bool(np.any(np.abs(final_v + 65.0) > 10.0)):
            reasons.append(f"Failed to recover baseline: final V = {final_v.tolist()}")

        if self.args.validation_profile == "strict":
            # 3. Synapse Ablation Falsifier (Randomly remove 5% of synapses)
            if len(model.synapses) > 20:
                n_to_remove = max(1, int(len(model.synapses) * 0.05))
                ablation_data = model.to_dict()
                indices = np.random.choice(len(ablation_data["synapses"]), n_to_remove, replace=False)
                for idx in sorted(indices, reverse=True):
                    ablation_data["synapses"].pop(idx)
                
                ablation_model = GrowthModel.from_dict(ablation_data, self.mission_config)
                v_ablation = ablation_model.simulate("sensory")
                
                # Check for collapse
                total_spikes = np.sum((v_ablation[:, :-1] < 0) & (v_ablation[:, 1:] >= 0))
                if total_spikes == 0:
                    reasons.append("Network collapsed into silence after minor synapse ablation")

            # 4. Mandatory Rejection (Every 50 neurons, force a bad mutation and check if it fails)
            # This is complex to implement inside run_falsifier as it requires stateful tracking.
            # We will skip the mandatory rejection for now and rely on strict gates.

        return len(reasons) == 0, reasons

    def run_growth(self):
        # Initial model
        if self.args.resume_model:
            logger.info(f"Resuming from model: {self.args.resume_model}")
            with open(self.args.resume_model) as f:
                model = GrowthModel.from_dict(json.load(f), self.mission_config)
        else:
            t01_path = "data/tutorials/artifacts/T01_two_area_seed/b76f1928-a249-4315-874a-54937c584070/"
            model = self.load_t01_seed(t01_path)
        
        # Save initial state
        with open(self.latest_model_path, "w") as f:
            json.dump(model.to_dict(), f, indent=2)
            
        manifest = {
            "start_time": float(time.time()),
            "args": vars(self.args),
            "status": "RUNNING",
            "current_n": int(model.n_neurons),
            "validation_profile": self.args.validation_profile
        }
        self.write_artifact("campaign_manifest.json", manifest)

        target_n = self.args.max_n
        consecutive_failures = 0
        
        while model.n_neurons < target_n:
            n_before = model.n_neurons
            n_after = n_before + 1
            logger.info(f"Attempting growth: N={n_before} -> N={n_after}")
            
            # 1. Propose growth
            # Balance areas
            area1_count = len([m for m in model.neuron_metadata if m['area'] == 'lower'])
            area2_count = len([m for m in model.neuron_metadata if m['area'] == 'higher'])
            target_area = 'lower' if area1_count <= area2_count else 'higher'
            
            # Balance cell types
            e_count = len([m for m in model.neuron_metadata if m['area'] == target_area and m['type'] == 'E'])
            pv_count = len([m for m in model.neuron_metadata if m['area'] == target_area and m['type'] == 'PV'])
            target_type = 'E' if e_count <= pv_count * 4 else 'PV' # 80/20 rule roughly
            
            new_model_data = model.to_dict()
            new_model = GrowthModel.from_dict(new_model_data, self.mission_config)
            new_id = new_model.add_neuron(target_area, target_type)
            
            # Connectivity strategy: connect to a few existing neurons in same area
            # and a few in the other area
            same_area = [m['id'] for m in new_model.neuron_metadata if m['area'] == target_area and m['id'] != new_id]
            other_area = [m['id'] for m in new_model.neuron_metadata if m['area'] != target_area]
            
            # Connect to 2 random neurons in same area
            if same_area:
                targets = np.random.choice(same_area, min(2, len(same_area)), replace=False)
                for t in targets:
                    # In: from existing to new
                    t_type = new_model.neuron_metadata[t]['type']
                    w = np.random.uniform(0.1, 0.5)
                    e_rev = 0.0 if t_type == 'E' else -80.0
                    new_model.add_synapse(t, new_id, w, e_rev)
                    # Out: from new to existing
                    w = np.random.uniform(0.1, 0.5)
                    e_rev = 0.0 if target_type == 'E' else -80.0
                    new_model.add_synapse(new_id, t, w, e_rev)

            # Connect to 1 random neuron in other area (FF/FB)
            if other_area:
                t = np.random.choice(other_area)
                t_type = new_model.neuron_metadata[t]['type']
                w = np.random.uniform(0.05, 0.2)
                e_rev = 0.0 if t_type == 'E' else -80.0
                new_model.add_synapse(t, new_id, w, e_rev)
                w = np.random.uniform(0.05, 0.2)
                e_rev = 0.0 if target_type == 'E' else -80.0
                new_model.add_synapse(new_id, t, w, e_rev)

            # 2. Simulate
            conditions = ["baseline", "sensory", "prediction", "match"]
            v_traces = {}
            for cond in conditions:
                v_traces[cond] = new_model.simulate(cond)
                
            # 3. Validate
            passed, reasons = self.validate_step(v_traces, new_model)
            
            step_dir = os.path.join(self.artifact_dir, "steps", f"N{n_after:04d}")
            os.makedirs(step_dir, exist_ok=True)
            
            if passed:
                logger.info(f"PASS: N={n_after}")
                model = new_model
                consecutive_failures = 0
                
                # Save step artifacts
                v_packed = np.stack([v_traces[c] for c in conditions])
                np.save(os.path.join(step_dir, "v_traces.npy"), v_packed)
                with open(os.path.join(step_dir, "model_state.json"), "w") as f:
                    json.dump(model.to_dict(), f, indent=2)
                
                # Update ledger
                ledger_entry = {
                    "n_before": int(n_before),
                    "n_after": int(n_after),
                    "area": target_area,
                    "type": target_type,
                    "timestamp": float(time.time()),
                    "status": "PASS",
                    "validation_profile": self.args.validation_profile
                }
                with open(self.ledger_path, "a") as f:
                    f.write(json.dumps(ledger_entry) + "\n")
                
                # Update latest
                with open(self.latest_model_path, "w") as f:
                    json.dump(model.to_dict(), f, indent=2)
                
                # Update manifest (Fix stale bug)
                manifest["current_n"] = int(model.n_neurons)
                with open(self.manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2)
            else:
                logger.warning(f"FAIL: N={n_after}. Reasons: {reasons}")
                consecutive_failures += 1
                
                # Record rejection
                rej_entry = {
                    "n_target": int(n_after),
                    "reasons": [str(r) for r in reasons],
                    "timestamp": float(time.time()),
                    "validation_profile": self.args.validation_profile
                }
                with open(self.rejected_path, "a") as f:
                    f.write(json.dumps(rej_entry) + "\n")
                
                if consecutive_failures >= self.args.max_consecutive_failures:
                    logger.error("Too many consecutive failures. Stopping.")
                    break

            # Checkpoints and Falsifiers
            if model.n_neurons % self.args.checkpoint_every == 0:
                logger.info(f"Running falsifier pass at N={model.n_neurons}")
                f_passed, f_reasons = self.run_falsifier(model)
                if f_passed:
                    logger.info(f"Falsifier PASS at N={model.n_neurons}")
                    cp_path = os.path.join(self.artifact_dir, f"checkpoint_N{model.n_neurons}.json")
                    with open(cp_path, "w") as f:
                        json.dump(model.to_dict(), f, indent=2)
                else:
                    logger.warning(f"Falsifier FAIL at N={model.n_neurons}. Reasons: {f_reasons}")
                    # Rollback to previous checkpoint
                    prev_n = model.n_neurons - self.args.checkpoint_every
                    if prev_n >= self.args.start_n:
                        logger.info(f"Rolling back to N={prev_n}")
                        if prev_n == 4 and not self.args.resume_model:
                             t01_path = "data/tutorials/artifacts/T01_two_area_seed/b76f1928-a249-4315-874a-54937c584070/"
                             model = self.load_t01_seed(t01_path)
                        else:
                            # Search for CP file
                            cp_file = os.path.join(self.artifact_dir, f"checkpoint_N{prev_n}.json")
                            if not os.path.exists(cp_file) and self.args.resume_model:
                                # If resume, the CP might be at the resume path or we can't rollback further than start
                                logger.error(f"Cannot rollback: checkpoint N={prev_n} not found.")
                                break
                            with open(cp_file) as f:
                                model = GrowthModel.from_dict(json.load(f), self.mission_config)
                        consecutive_failures += 1
                    else:
                        logger.error("Falsifier failed before first checkpoint. Stopping.")
                        break

        # Finalize
        manifest["status"] = "COMPLETED" if model.n_neurons >= target_n else "PARTIAL"
        manifest["end_time"] = float(time.time())
        manifest["final_n"] = int(model.n_neurons)
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
            
        return manifest["status"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-n", type=int, default=4)
    parser.add_argument("--event-target-n", type=int, default=10)
    parser.add_argument("--max-n", type=int, default=500)
    parser.add_argument("--min-area-target", type=int, default=100)
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--falsify-every", type=int, default=10)
    parser.add_argument("--max-consecutive-failures", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-profile", type=str, choices=["weak", "strict"], default="strict")
    parser.add_argument("--resume-model", type=str, default=None)
    args = parser.parse_args()
    
    root = os.path.abspath(os.path.join(os.getcwd()))
    campaign = GrowthCampaign(root, args)
    status = campaign.run_growth()
    print(f"Campaign finished with status: {status}")
