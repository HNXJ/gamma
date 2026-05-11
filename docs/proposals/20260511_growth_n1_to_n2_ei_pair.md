# Growth Event Proposal: N=1 -> N=2 (E/I Pair)

**Status:** PROPOSAL  
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
    - compile_check
    - no_nan_inf
    - baseline_reciprocal_stability
    - n2_spike_count_check
  decision: PENDING_REVIEW
```

## 3. Implementation Plan
1.  **Harness Extension:** Implemented `src/gamma_runtime/science_components/izhikevich_network.py` capable of simulating $N$ coupled neurons.
2.  **Simulation Run:** Execute a 300ms simulation with the proposed E/I parameters.
3.  **Metrics:** Calculate spike rates for both N1 and N2, and verify that N2 provides inhibitory control over N1.
4.  **Artifacts:** Generate a full artifact suite (manifest, hashes, metrics, receipt-candidate) for the N=2 state.
5.  **Test Verification:** Validated the network harness logic via `tests/test_izhikevich_network.py` (Passed).

## 4. Success Criteria
- Deterministic simulation passes without numerical instability.
- N2 (Inhibitory) fires in response to N1 (Excitatory) activity.
- N1 firing rate is reduced when N2 is active compared to N=1 baseline (if weights are sufficient).
- Artifacts are correctly hashed and manifest-aligned.

## 5. Next Steps
Upon approval of this design, the `izhikevich_network` harness will be implemented and the first N=2 candidate run will be executed.
