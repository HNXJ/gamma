# JAXFNE Local Install Request

This is a scaffold for a future worker task to install JAXFNE locally for Gamma Labyrinth:

- **Target Repo:** `https://github.com/HNXJ/jaxfne.git`
- **Verification:** Worker must choose the branch/tag after verification (v0.3.x dev vs stable).
- **Environment:** Install in an isolated venv or editable local source.
- **Validation:** 
  - Run import/version smoke tests.
  - Inventory examples and tutorials.
- **Constraints:**
  - DO NOT run scientific simulations.
  - Write receipt artifacts.
  - Report exact version/head.

## Fulfillment Status

**Status:** Fulfilled

**Resolution:** 
Python 3.11.15 was installed via Homebrew. An isolated `venv` was created, and `jaxfne` was successfully installed in editable mode from the local clone. Import smoke test passed for version `0.3.5`. No simulations were run, and no numerical/scientific results were validated. Players may now propose bounded import-based tools, example inventories, notebook stubs, validators, and mission cards.
