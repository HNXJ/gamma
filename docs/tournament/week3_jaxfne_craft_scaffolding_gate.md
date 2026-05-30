# Week 3 JAXFNE Craft Scaffolding Gate

## 1. Status Block
- **Tournament ID:** jaxfne_craft_tournament_3month_2026q2q3
- **Week:** 3
- **Plane:** Control / Implementation Gate
- **Truth Status:** truth_safe_unverified
- **Repo:** D:\workspace\gemini-gamma-labyrinth\repos\gamma
- **Branch:** office-dev
- **Commit:** f892d480a8548d2efc24080f2192917ce463996f
- **Prior Week Closure:** WEEK2_CLOSED_GROUNDED_AUDIT_EVIDENCE_ACCEPTED

## 2. Scope
Week 3 converts grounded audit evidence into a bounded implementation plan for JAXFNE craft scaffolding. The focus is on hardening the architectural foundations—interfaces, validation, and reporting—identified as gaps in the Week 2 inventory audit. This gate does not authorize biological simulations, Truth-plane mutations, or dependency installations.

## 3. Evidence Inputs
The following Week 2 artifacts were inspected to form this gate:
- `outputs/tournament/week2_jaxfne_inventory_audit_grounded/evidence_scope_correction.md` (Decision: ACCEPT)
- `outputs/tournament/week2_jaxfne_inventory_audit_grounded/theta_lite_grounded_review.md` (Decision: ACCEPT)
- `outputs/tournament/week2_jaxfne_inventory_audit_grounded/manifest.json` (Decision: ACCEPT)
- `docs/tournament/week2_jaxfne_16_agent_inventory_audit_launch.md` (Decision: PASS)

## 4. Confirmed Facts from Week 2
- **JAXFNE Source Version:** 0.3.14 observed in `pyproject.toml`.
- **Import Status:** JAXFNE import passes when run within the inventory root; Jaxley remains **ABSENT** (`ModuleNotFoundError`).
- **Runtime Admission:** Gemma 4 A26B (`gemma-4-26b-a4b-it`) is admitted for 16-agent concurrent short-smoke tasks.
- **Placeholder Boundaries:** `jaxfne/bridges.py` is confirmed as a scaffold with active `NotImplementedError` placeholders (e.g., HH reference).
- **Audit Grounding:** Week 2 reports were successfully rerun with grounded file snippets, resolving the initial `PATH_ONLY` downgrade.

## 5. Week 3 Implementation Themes
- **Optional Dependency Hygiene:** Hardening the Jaxley boundary to ensure graceful failures and informative diagnostics.
- **Placeholder-Fails-Loudly Contract:** Auditing and repairing internal placeholders to ensure they raise appropriate errors instead of returning silent nulls.
- **JSON-Safe Reporting:** Standardizing the manifest and I/O layer to ensure all JAX/Numpy types are correctly serialized.
- **Scaffold Mapping:** Formalizing the source-to-field and readout bridge contracts based on audited file structures.
- **Verification Provenance:** Ensuring every implementation step is backed by command-line evidence and hashed artifacts.

## 6. Proposed Bounded Implementation Tasks

### W3-T1: Jaxley Optional Boundary and Import Diagnostics
- **ID:** W3-T1
- **Path:** `D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne`
- **Files Allowed:** `jaxfne/bridges.py`, `jaxfne/__init__.py`
- **Scope:** Enhance `require_jaxley()` and similar guards to provide unified, version-aware import error messages.
- **Non-Scope:** Installing Jaxley or implementing Jaxley-dependent logic.
- **Validation:** `python -c "import jaxfne; jaxfne.bridges.require_jaxley()"` must fail loudly with the expected message.

### W3-T2: Placeholder-Fails-Loudly Audit Repair
- **ID:** W3-T2
- **Path:** `D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne`
- **Files Allowed:** `jaxfne/*.py`
- **Scope:** Replace silent `pass` or `return None` in critical scaffold paths with `NotImplementedError` or contract-aligned placeholders.
- **Non-Scope:** Implementing the actual missing logic.
- **Validation:** `grep -r "pass" jaxfne/` and manual review of changed paths.

### W3-T3: JSON-Safe Manifest/Report Validator
- **ID:** W3-T3
- **Path:** `D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne`
- **Files Allowed:** `jaxfne/io.py`, `jaxfne/validation.py`
- **Scope:** Hardening `json_safe` to handle complex JAX tracers and ensuring `manifest()` includes all Week 2 evidence metadata.
- **Non-Scope:** Changing the base manifest schema version without authorization.
- **Validation:** `python jaxfne/io.py` smoke test with mixed JAX/Numpy objects.

### W3-T4: Source-to-Field/Readout Scaffold Map
- **ID:** W3-T4
- **Path:** `D:\workspace\gemini-gamma-labyrinth\repos\gamma\docs\tournament`
- **Files Allowed:** `docs/tournament/week3_scaffold_map.md`
- **Scope:** Create a technical map of the tensor-flow contracts between `emitters.py`, `bridges.py`, and `fields.py`.
- **Non-Scope:** Mutating code.
- **Validation:** Internal THETA-lite consistency review.

### W3-T5: Local Smoke-Test Suite Design
- **ID:** W3-T5
- **Path:** `D:\workspace\gemini-gamma-labyrinth\repos\gamma\scripts`
- **Files Allowed:** `scripts/week3_smoke_suite.py`
- **Scope:** Design a wrapper script that executes the existing `test_api_smoke.py` and inventory-root import checks.
- **Non-Scope:** Running full JAX simulations.
- **Validation:** Successful execution of the suite.

### W3-T6: Week 3 THETA Acceptance Checklist
- **ID:** W3-T6
- **Path:** `D:\workspace\gemini-gamma-labyrinth\repos\gamma\outputs\tournament`
- **Files Allowed:** `outputs/tournament/week3_theta_checklist.md`
- **Scope:** Define the criteria for closing Week 3.
- **Validation:** Self-referential check.

## 7. Branch and Artifact Policy
- **Branch:** `office-dev` only.
- **Git Policy:** No force-push; no stash mutation; no overwriting unowned tracked changes.
- **Provenance:** Every implementation turn must be verified with shell output, manifest updates, and SHA256 hashes.
- **Truth Status:** All implementation artifacts remain `truth_safe_unverified`.

## 8. Validation Command Templates
- `git -C <repo> status --short --branch`
- `python -m py_compile <changed_files>`
- `python -c "import jaxfne; ..."`
- `Get-FileHash <artifact> -Algorithm SHA256`

## 9. Week 3 Stop Conditions
- **Branch Mismatch:** Any attempt to work outside `office-dev`.
- **Credential Exposure:** Immediate stop if secret-like material appears.
- **Biological Interpretation:** Any claim of biological validity or E/I mechanism truth.
- **Silent Failure:** Any placeholder found to return success/None instead of failing loudly.
- **Drift:** Implementation straying into JAX simulation without authorization.

## 10. Week 3 Decision
**READY_FOR_WEEK3_BOUNDED_IMPLEMENTATION_TASKS**

## 11. Next Safe Action
Assign the first implementation worker to task **W3-T1** (Jaxley Optional Boundary) after this gate document is committed and reviewed.

---
[unknown_model_do_not_guess][D:\workspace\gemini-gamma-labyrinth\repos\gamma][20260530-0845]
