# Gamma Stack Canonical Specification

This document defines the structural doctrines, operational invariants, and canonical extraction heuristics required to keep the Gamma stack config-driven, fail-fast, and extraction-hungry.

## 1. Operational Invariants (Hard Doctrine)
These are not style notes; they are permanent operational invariants.
* **Never** treat memory as runtime truth.
* **Never** guess ports when config exists.
* **Never** claim "running" because a port bound.
* **Never** treat readable HTTP status as a writable control surface.
* **Never** mark a placeholder as implemented.
* **Never** start runtime work without preflight if startup/inference is involved.
* **Never** debug council semantics before model availability is confirmed.
* **Never** silently mix dashboard port, hub port, and LMS port.

## 2. Scoped Authorization Policies
Pre-authorize the safe scope, not the whole machine, to reduce permission drag without reducing safety.

### Inside Workspace (`/Users/hamednejat/workspace/`)
**ALLOWED:** reads, writes, replace, shell, git, tests, local scripts, skill activation, config edits.

### Inside Office Mac (`/Users/HN/MLLM/`)
**ALLOWED:** SSH read/write/test/git operations, service checks, curl, model/load checks, log inspection.

### Approvals Required
Destructive actions outside scope, credential changes, system-wide package changes outside project venv, broad `rm -rf`, `sudo`, disk utilities, chmod recursion.

## 3. Canonical Tools
Tools move repeated reasoning into stable entrypoints to reduce execution friction.
* `/capabilities-audit` - Verifies tools, modes, permissions, shell, bounds, interpreter, and policy tier.
* `/beta` - Read-only compact audit emitting strict JSON and evidence classes.
* `/alpha` - Smallest local corrective repair after Beta validation.
* `/gamma` - Execution mode (only allowed after preflight passes).
* `/theta` - Postmortem mode comparing expected vs observed.
* `/port-audit` - Reports configured ports, hardcoded literals, service roles, and drift.
* `/model-audit` - Reports requested model key, resolved runtime name, load state, and blockers.
* `/stream-audit` - Reports schema presence, runtime emission, monitor consumption, and UI.
* `/inventory-audit` - Checks player inventory roots, files, schemas, and latest artifacts.
* `/parity-audit` - Compares memory, config, code, remote runtime, and remote control surfaces.
* `/startup-verify` - Runs preflight and startup truth criteria (no mission launch).
* `/endpoint-discover` - Reads served HTML/JS to extract actual backend routes.
* `/remote-diff` - Compares local repo state vs remote branch/runtime surfaces.

## 4. Canonical Code Modules
Duplicated mechanics that should become modules, linters, or assertions.
* `src/gamma_runtime/preflight.py` - Central preflight and failure reasons.
* `src/gamma_runtime/config.py` - Canonical host/port/config surface.
* `src/gamma_runtime/surfaces.py` - Defines observation, control, runtime status, SSH, and model surfaces.
* `src/gamma_runtime/identity.py` - Role-distinct resolved runtime names.
* `src/gamma_runtime/provenance.py` - Execution and stream schemas.
* `src/gamma_runtime/audit_assertions.py` - Placeholder detection, evidence separation, truth inflation checks.
* `src/gamma_runtime/inventory_schema.py` - Validates memory.md, latest_state.json, etc.
* `src/gamma_runtime/model_readiness.py` - Separates endpoint reachable from model loaded.

## 5. Canonical Skills
Skills reduce rediscovery of operational rules. 
* `evidence-surface-grounding`
* `flash-agent-preflight`
* `gamma-port-canonicalization`
* `startup-truth-criteria`
* `runtime-surface-classification`
* `lms-model-readiness-gate`
* `inventory-schema-discipline`
* `structured-event-bridge`
* `compact-audit-design`
* `role-memory-task-layering`
* `gamma-branch-parity-audit`

## 6. The Extraction Protocol
At the end of every major repair/audit pass, the system must evaluate skill/module extraction.

### Extraction Heuristic
Extract into a skill/module if the logic crosses the threshold of:
`recurrence × hazard × rediscovery cost × blast radius`
(e.g., used twice, caused a major failure, has a high blast radius, encodes a truth discipline, or is likely to recur).

### Required Closing Sections
Every pass must end with the generation of these two sections:

#### `skills-to-make` (For doctrine and reusable workflows)
```yaml
- name: 
- class: audit_doctrine | cli_surface | memory_policy
- trigger_conditions: 
- purpose: 
- implementation_home: 
- enforcement_home: 
- documentation_home: 
- acceptance_tests: 
- anti_regression_hook: 
- blast_radius: 
```

#### `code-to-extract` (For duplicated mechanics)
Identify code blocks that should become code modules, linters, or audit assertions, explicitly separating them from prose-based skill doctrine.