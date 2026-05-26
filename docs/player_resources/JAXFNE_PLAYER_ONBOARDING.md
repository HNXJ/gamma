# JAXFNE Player Onboarding

This is a scaffold for players.

- Local JAXFNE is not installed on the Office Mac as of this check.
- Public upstream context says JAXFNE is a JAX-native source-to-field/readout engine for TFNE.
- Public API grammar: `Emitter -> Source -> Field -> Probe -> Objective -> Optimizer`.
- Public install text distinguishes stable PyPI and dev source; exact local version must be verified after install.

Players may propose mission cards, validators, receipt checks, notebook stubs, and import probes.
Players may not claim numerical/biological/scientific results.
Players may not claim N=4 unlock.

Truth status: `truth_safe_unverified`.

## Local Office Mac JAXFNE Status

- **Repo status:** cloned (`/Users/HN/gamma-world/external/jaxfne`)
- **Branch/Head:** `main` / `236531c597e1c9b1a7b1f5628c8059d13ed2c85f`
- **Version/Import Status:** import failed (`ModuleNotFoundError` for `jax`)
- **Venv Status:** isolated venv created (`jaxfne-smoke`) but pip install failed due to Python version requirement (requires `>=3.10`, system has `3.9.6`).
- **Examples Inventory:** 25 docs, 10 notebooks found. Candidate tutorials: `test_v031_single_neuron_tutorial.py`, `test_v032_parameter_sweep_tutorial.py`, `test_v035_small_recurrent_ei_tutorial.py`.

*Caveat:* Local import smoke is tooling evidence only. No JAXFNE numerical simulation or scientific result has been validated.
