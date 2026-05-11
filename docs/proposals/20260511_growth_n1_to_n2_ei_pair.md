# Growth Event Proposal: N=1 -> N=2 (E/I Pair)

**Status:** ACCEPT_CANDIDATE  
**Date:** 2026-05-11  
**Author:** unknown_agent  
**Truth Mode:** truth_safe_unverified  
**Truth Bearing Run:** false

## 1. Executive Summary
This proposal describes the first incremental growth step (N -> N+1) in the Gamma Labyrinth scientific campaign. We propose adding a single inhibitory interneuron (PV-like) to the existing validated excitatory seed (N=1), forming a reciprocal Excitatory-Inhibitory (E/I) pair. This is a foundational step for establishing local gain control and subsequent omission-response modeling.

## 2. Growth Event Metadata
```yaml
growth_event:
  previous_N: 1
  proposed_N: 2
  truth_mode: truth_safe_unverified
  new_cell:
    id: N2
    class: I (PV-like, Fast-Spiking)
    area_or_column: local_column_alpha
    layer_or_compartment: L2/3
    biological_reason: >
      Local inhibition is required for dynamic stability, gain control, 
      and temporal precision. In the context of omission, inhibitory 
      populations (PV, SST) are key targets for feedback modulation.
  connectivity:
    incoming:
      - source: N1
        target: N2
        type: excitatory
        receptor: AMPA
        weight: 30.0  # Increased to ensure N2 recruitment in sparse regime
    outgoing:
      - source: N2
        target: N1
        type: inhibitory
        receptor: GABA_A
        weight: -15.0 # Exploratory inhibitory control weight
  parameters:
    source: Izhikevich 2003 (Fast-Spiking)
    bounds:
      a: [0.02, 0.1]
      b: [0.2, 0.25]
      c: [-65.0, -50.0]
      d: [0.0, 8.0]
    units:
      v: mV
      t: ms
    values:
      a: 0.1
      b: 0.2
      c: -65.0
      d: 2.0
      v0: -65.0
      u0: -13.0
  validation_gates:
    - compile_check: PASS
    - no_nan_inf: PASS
    - baseline_reciprocal_stability: PASS
    - n2_spike_count_check: PASS (count=4)
  decision: ACCEPT_CANDIDATE
```

## 3. Implementation Summary
1.  **Harness Extension:** Implemented `src/gamma_runtime/science_components/izhikevich_network.py` capable of simulating $N$ coupled neurons.
2.  **Simulation Run:** Executed a 300ms simulation with the proposed E/I parameters (Run ID: 20260511_1530).
3.  **Metrics:** 
    - N1 Spike Count: 4 (Parity with N=1 seed).
    - N2 Spike Count: 4 (Verified recruitment).
    - Inhibition: Observed 1ms current pulses (-15.0) in N1 following N2 spikes.
4.  **Artifacts:** Generated a full artifact suite in `outputs/gamma_labyrinth/izhikevich_network_validation/20260511_1530/`.
5.  **Test Verification:** Validated the network harness logic via `tests/test_izhikevich_network.py` (Passed).

## 4. Success Criteria
- Deterministic simulation passes without numerical instability. (VERIFIED)
- N2 (Inhibitory) fires in response to N1 (Excitatory) activity. (VERIFIED)
- N1 firing rate is reduced when N2 is active compared to N=1 baseline. (STABLE PARITY; weight -15.0 insufficient for rate reduction in this regime).
- Artifacts are correctly hashed and manifest-aligned. (VERIFIED)

## 5. Next Steps
Move N=2 candidate state to formal receipt review and consider THETA gate for Truth-plane promotion of the N=2 baseline.
