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

**Status:** Blocked

**Blocker:** Installation failed because `jaxfne` requires Python `>=3.10`, but the Office Mac system Python is `3.9.6`. 

**Next Smallest Repair:** 
Install a compatible Python version (e.g. Python 3.10, 3.11, or 3.12) on the Office Mac via `homebrew`, `pyenv`, or `conda`, and re-attempt the isolated `venv` creation and installation.
