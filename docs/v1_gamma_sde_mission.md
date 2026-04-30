# Game of Tokens: V1-Gamma-Schiz Mission

**Objective:** Discover a Pareto frontier between Healthy and Schizophrenia-like laminar V1 regimes.
**Phenotype:** Reduced evoked gamma relative to baseline and weaker phase organization, driven primarily by PV/GABA parameters.

## Architecture & Constraints
- **Laminar Prior:** Direct sensory drive to both L4 and L5, with delayed L2/3 recruitment (Nejad 2025).
- **Pathology Axis:** PV/GABA dysfunction and inhibitory decay kinetics (Uhlhaas & Singer).
- **Interpretation Constraint:** A V1 evoked-gamma discovery engine, not full predictive-coding pathology (Westerberg 2025).

## The SDE Game Setup
- **Proponent:** Proposes mechanistically grounded healthy/schiz parameter sets.
- **Adversary:** Falsifies unstable, dead, or brittle candidates.
- **Consensus:** Judges and selects the best frontier pairs.

## Execution
Use `scripts/overnight_consensus.py --run_type sde --team v1_gamma_sde_team` to launch the debate, and refer to `jbiophys` for all mathematical verification and PSD evaluation.