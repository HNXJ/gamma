# Growth Event Proposal: N=2 -> N=3 (E/I/I Trio - Dendritic Gating)

**Status:** ACCEPT_CANDIDATE  
**Date:** 2026-05-11  
**Author:** unknown_agent  
**Truth Mode:** truth_safe_unverified  
**Truth Bearing Run:** false

## 1. Executive Summary
This proposal describes the second incremental growth step (N -> N+1) in the Gamma Labyrinth scientific campaign. We propose adding a third neuron, an inhibitory Low-Threshold Spiking (LTS) interneuron (SST-like), to the existing validated E/I pair (N=2). This establishes the "Dendritic Gating" node, allowing us to model the dissociation between perisomatic (PV) and dendritic (SST) inhibition, a key mechanism for spectral field modulation and top-down expectation.

## 2. Growth Event Metadata
```yaml
growth_event:
  previous_N: 2
  proposed_N: 3
  truth_mode: truth_safe_unverified
  new_cell:
    id: N3
    class: I (SST-like, Low-Threshold Spiking)
    area_or_column: local_column_alpha
    layer_or_compartment: L2/3 (Dendritic targeting)
    biological_reason: >
      SST interneurons provide dendritic gating and are implicated in 
      low-frequency (alpha/beta) field modulation. Adding SST allows 
      separating gain control (PV) from state gating (SST).
  connectivity:
    incoming:
      - source: N1
        target: N3
        type: excitatory
        receptor: AMPA
        weight: 20.0  # Exploratory recruitment weight
    outgoing:
      - source: N3
        target: N1
        type: inhibitory
        receptor: GABA_B (Proxy via slower weight/timescale if modeled, or GABA_A for now)
        weight: -10.0 # Dendritic inhibition proxy
  parameters:
    source: Izhikevich 2003 (Low-Threshold Spiking)
    bounds:
      a: [0.01, 0.05]
      b: [0.2, 0.3]
      c: [-65.0, -50.0]
      d: [0.0, 4.0]
    units:
      v: mV
      t: ms
    values:
      a: 0.02
      b: 0.25
      c: -65.0
      d: 2.0
      v0: -65.0
      u0: -16.25 # b * v0
  validation_gates:
    - compile_check: PASS
    - no_nan_inf: PASS
    - trio_stability: PASS
    - n3_recruitment_check: PASS (count=4)
  decision: ACCEPT_CANDIDATE
```

## 3. Implementation Summary
1.  **Simulation Run:** Executed a 300ms simulation with the E-PV-SST trio (Run ID: 20260511_1545).
2.  **Metrics:** 
    - N1 Spike Count: 4.
    - N2 Spike Count: 4.
    - N3 Spike Count: 4 (Verified recruitment).
3.  **Artifacts:** Generated full artifact suite in `outputs/gamma_labyrinth/izhikevich_network_validation/20260511_1545/`.
4.  **Verification:** Confirmed N3 (SST) recruitment and stable dynamics in the presence of N2 (PV).

## 4. Success Criteria
- Deterministic simulation passes. (VERIFIED)
- N3 (SST) fires in response to N1 (Excitatory) activity. (VERIFIED)
- N1-N2-N3 ensemble remains numerically stable. (VERIFIED)
- Artifacts correctly hashed and manifest-aligned. (VERIFIED)

## 5. Next Steps
Move to N=4 growth proposal: adding a VIP-like interneuron to implement the disinhibitory mechanism (VIP -> SST).
