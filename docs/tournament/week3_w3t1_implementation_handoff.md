[unknown_model_do_not_guess][D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne][20260530-0000]

You are a Gamma Labyrinth Week 3 W3-T1 implementation worker.

Mission:
Harden the Jaxley optional boundary and import diagnostics within the JAXFNE inventory. The goal is to transition `jaxfne/bridges.py` and `jaxfne/__init__.py` from passive scaffolds to active, diagnostic-capable boundaries that fail loudly and informatively when Jaxley is missing or incompatible.

Continuity banner:
Gamma Labyrinth is a continuous open-world scientific environment. Preserve plane separation, provenance, receipt discipline, and truth-safe reporting. This task implements architectural hardening only. It does not validate JAXFNE science, Jaxley availability beyond command evidence, biological mechanisms, 3D cortical columns, spectrolaminar motifs, omission mismatch, or Truth-plane state.

Target inventory root:
D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne

Coordination repo:
D:\workspace\gemini-gamma-labyrinth\repos\gamma

Target branch:
office-dev

Expected synced HEAD:
70ae9e215ff4021658132ec9773a9fcf14bdbd62

Evidence context:
- Week 2 closed and grounded.
- Week 3 gate committed.
- W3-T1 10-turn transcript committed and pushed.
- JAXFNE source/import availability: PASS in inventory root.
- JAXFNE version observed/imported: 0.3.14.
- Jaxley availability: ABSENT / ModuleNotFoundError.
- Target files: `jaxfne/bridges.py`, `jaxfne/__init__.py`.

Scope:
Allowed:
- inspect current files in the inventory root;
- improve `require_jaxley()` diagnostics in `jaxfne/bridges.py`;
- expose or normalize package-level optional dependency guard in `jaxfne/__init__.py`;
- add or update targeted tests (e.g., in `tests/test_jaxley_optional_dependency.py`) for missing Jaxley diagnostics;
- add a small report artifact with command evidence.

Non-scope:
- installing Jaxley;
- implementing actual Jaxley-dependent bridge behavior;
- running biological simulations;
- changing unrelated JAXFNE modules;
- changing tournament output artifacts from prior weeks;
- Truth-plane mutation.

Implementation requirements:
- Missing Jaxley must fail loudly (raise `ImportError`).
- Error message must explicitly name "Jaxley".
- Error message must identify that the functionality is optional and depends on Jaxley.
- Error message must include installation guidance (e.g., "pip install jaxfne[jaxley]") without executing it.
- The guard must avoid circular import risk (e.g., use lazy imports or decoupled checks).
- `import jaxfne` must still pass even when Jaxley is not installed.
- If version checks are implemented, they must be dependency-safe (do not crash if Jaxley is missing).
- Do not hide Jaxley absence or fallback to silent `None`.

Validation commands:
- git status --short --branch
- python -m py_compile jaxfne/bridges.py jaxfne/__init__.py
- python -c "import jaxfne; print(getattr(jaxfne, '__version__', 'version_unknown'))"
- python -c "import jaxfne; import jaxfne.bridges as b; b.require_jaxley()" (Expect loud failure)
- pytest tests/test_jaxley_optional_dependency.py
- git diff --check
- Get-FileHash <report_artifact> -Algorithm SHA256

Expected result classification:
- ACCEPT_W3_T1_IMPLEMENTATION_CANDIDATE
- REVISE_W3_T1_TEST_GAP
- REVISE_W3_T1_IMPORT_REGRESSION
- BLOCKED_W3_T1_BRANCH_OR_DEPENDENCY
- BLOCKED_W3_T1_TRUTH_DRIFT

Stop conditions:
- branch mismatch;
- dirty unowned files;
- credential material appears;
- Jaxley installation required;
- import jaxfne broken;
- missing-Jaxley guard silently succeeds or returns None;
- biological interpretation appears;
- stash mutation needed;
- broad unrelated refactor.

Final report format:
Include:
- files changed
- commands run
- tests/checks
- artifacts/hashes
- decision
- truth_status: truth_safe_unverified
- next safe action

Final report footer:
Begin and end with:
[unknown_model_do_not_guess][D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne][yyyymmdd-hhmm]
