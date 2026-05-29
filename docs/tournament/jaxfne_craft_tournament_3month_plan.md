# JAXFNE Craft Tournament: 3D Cortical Columns, Cortex Simulation Validation, and Spectrolaminar/Omission Mismatch Tasks

```text
[unknown_model_do_not_guess][unknown_root_do_not_guess][20260529-0000]
```

## Status Block

| Field | Value |
|---|---|
| **Document type** | Gamma Labyrinth tournament-control plan |
| **Tournament ID** | `jaxfne_craft_tournament_3month_2026q2q3` |
| **Date** | 2026-05-29 |
| **Duration** | 3 months / 12 weeks |
| **Plane** | Control / Planning |
| **Truth status** | `truth_safe_unverified` |
| **Primary mode** | ALPHA planning -> GAMMA bounded execution -> THETA validation |
| **Public/private status** | Private Control-plane document unless explicitly redacted and approved |
| **Primary repos** | `gamma`, `gamma-protocol`, `gamma-analysis`, `gamma-science`, `gamma-tools`, `gamma-arena` |
| **Target file** | `docs/tournament/jaxfne_craft_tournament_3month_plan.md` |

---

## 1. Continuity Banner

Gamma Labyrinth is a continuous open-world scientific environment where harnessed AI agents use data, tools, and context to evaluate, analyze, simulate, model, and discover. Evidence and failures then improve tools, harnesses, inventories, context, and future scientific play.

The game never stops. It checkpoint-recovers and continues. Preserve strict separation among Control, Execution, Truth, Observation, Analysis, Science source, and Tooling. All scientific outputs remain `truth_safe_unverified` unless promoted through receipt-backed validation. No harness means no valid player run.

---

## 2. Mission

Create and run a 3-month Gamma Labyrinth tournament focused on **JAXFNE craft** for computational neuroscience and biophysics.

The tournament has three primary goals:

1. Develop stable solutions and implementation candidates for **3D cortical columns**.
2. Validate and test simulations and models of cortex through reproducible numerical and scientific gates.
3. Build and test **spectrolaminar motif** and **omission mismatch** tasks with explicit proposal-level interpretation and evidence discipline.

This document is a Control-plane tournament plan. It does not establish biological truth, accepted E/I mechanisms, accepted omission responses, or validated spectrolaminar mechanisms.

---

## 3. Doctrine Anchors

### 3.1 Gamma Labyrinth Loop

```text
data + tools + context
  -> evaluate / analyze / simulate / model / discover
  -> evidence / results / failures
  -> improved tools / context / harness / inventory
  -> next play
```

### 3.2 Agent and Harness Law

Agents are players only when admitted through an explicit harness/runtime contract. A harness is the player's inventory, craft table, runtime contract, and safety boundary.

Each valid player must declare:

- model/backend identity;
- API URL, local endpoint, or secure auth mode without exposing secrets;
- session identity;
- harness identity;
- allowed tools;
- artifact policy;
- transcript policy;
- truth mode;
- mock/live status;
- stop conditions.

### 3.3 Evidence Discipline

Tournament progress rewards:

- reproducible scientific work;
- tool improvement;
- falsification;
- negative-result preservation;
- manifests;
- hashes;
- validation;
- receipt candidates;
- direct local smoke execution;
- bounded interpretation.

Observation surfaces are not truth. Transcripts, dashboards, consensus, fluent reports, and issue comments may guide review, but they do not promote biological or runtime state into Truth-plane status.

### 3.4 Scientific Mission Anchor

The neuroscience startup mission remains computational neuroscience / biophysics, with emphasis on:

- E/I balance;
- omission and predictive-coding dynamics;
- sparse higher-order spiking;
- broad low-frequency field modulation;
- spike-field dissociation;
- post-event or post-omission gain/facilitation;
- incremental model growth.

JAXFNE/Jaxley craft is tool/model infrastructure progress unless validated by simulation artifacts and receipts.

---

## 4. Tournament Structure

| Month | Theme | Core Objective |
|---:|---|---|
| **Month 1** | Crafting foundations and harness readiness | Establish harnesses, repo safety, JAXFNE/Jaxley capability inventory, cortical-column specifications, and local smoke gates. |
| **Month 2** | Model growth, validation, and cortical-column stability | Build minimal candidates, validate stability, test cortical simulation behavior, and preserve failures. |
| **Month 3** | Spectrolaminar, omission mismatch, adversarial validation, and finals | Build tasks, run integrated challenges, conduct THETA review, and report accepted candidates/rejections/tool improvements. |

---

## 5. Tournament Roles

| Role | Plane | Responsibilities | Cannot Do |
|---|---|---|---|
| **Player agents** | Execution / Analysis | Submit bounded model, simulation, task, or tool artifacts. | Cannot become valid players without harness identity. |
| **Judge agents** | Control / Analysis | Review evidence, score submissions, detect drift, route revise/reject/block decisions. | Cannot promote truth by consensus. |
| **THETA validators** | Validation / Truth-gate review | Audit artifacts, manifests, hashes, numerical gates, provenance, and claim typing. | Cannot accept biological truth without receipt path. |
| **JAXFNE craft agents** | Tooling / Execution | Build source-to-field tensor bridge, readout contracts, JAX trace-safe utilities, JSON-safe manifests. | Cannot treat tool output as biological truth. |
| **Simulation/model agents** | Execution | Build and run cortical-column simulations under bounded task contracts. | Cannot overstate simulation outputs as accepted mechanisms. |
| **Analysis agents** | Analysis | Analyze transcripts, outputs, model behavior, benchmarks, negative results, and metrics. | Cannot mutate Truth-plane state. |
| **Science-source agents** | Science source | Ground assumptions in literature, define observables, identify parameter priors and task constraints. | Cannot treat project Markdown as peer-reviewed biology. |
| **Front/arena observation agents** | Observation | Display truth-safe tournament state and browser-visible evidence. | Cannot mutate state or hardcode scientific truth. |

---

## 6. Required Harness Identity for Every Player

Every tournament player must start with a harness declaration.

```yaml
player_harness:
  player_id: <agent_or_player_name>
  model_backend_identity: <exact_model_or_unknown_do_not_guess>
  endpoint_or_auth_mode: <api_url_or_local_runtime_without_secrets>
  session_id: <session_id>
  harness_id: <harness_id>
  allowed_tools:
    - <tool_or_repo_or_runtime>
  artifact_policy:
    manifest_required: true
    hashes_required: true
    command_trace_required: true
  transcript_policy:
    persist_or_flush_per_turn: true
    transcript_path: <path_or_unknown_do_not_guess>
  truth_mode: truth_safe_unverified
  mock_live_status: mock | live | unknown_do_not_guess
  claim_typing_required: true
  stop_conditions:
    - credential_risk
    - repo_or_branch_conflict
    - missing_artifact_persistence
    - mock_live_ambiguity
    - truth_mutation_without_receipt
    - unsupported_biological_interpretation
```

---

## 7. 12-Week Tournament Calendar

### Week 1 — Harness Admission and Capability Snapshot

**Goal:** Admit valid players and establish safe tournament state.

Required tasks:

- Verify repo paths, branches, and dirty state.
- Record player harness declarations.
- Snapshot JAXFNE/Jaxley capability surfaces.
- Identify active tests, notebooks, examples, and smoke paths.
- Establish a no-science-overclaim baseline.

Evidence package:

- repo/path/branch report;
- dirty-state report;
- harness manifest;
- capability inventory;
- initial risk ledger.

Stop condition:

- any player attempts tournament execution without harness identity.

---

### Week 2 — JAXFNE Craft Inventory

**Goal:** Define and validate the JAXFNE craft surface.

Required tasks:

- Audit source-to-field tensor bridge contracts.
- Audit emitter/readout contracts.
- Check JAX trace-safety for JIT-relevant paths.
- Run local smoke tests for existing craft paths.
- Audit placeholders: placeholder callables must fail loudly with a specific `NotImplementedError`.

Evidence package:

- contract inventory;
- direct smoke command outputs;
- placeholder audit results;
- test report;
- manifest and hashes for generated reports.

Stop condition:

- a placeholder returns silent success or dummy biological output.

---

### Week 3 — 3D Cortical-Column Specification

**Goal:** Produce a bounded specification for 3D cortical-column modeling.

Required tasks:

- Define coordinate systems.
- Define cortical layers and spatial bins.
- Define cell-class labels and proposal-level biological roles.
- Define connectivity schema.
- Define unit conventions.
- Define parameter provenance requirements.
- Define field/readout mapping assumptions.

Evidence package:

- specification document;
- schema candidate;
- parameter table;
- proposal/truth-status labels;
- review checklist.

Stop condition:

- a proposal-level layer/cell/mechanism assumption is written as accepted biological truth.

---

### Week 4 — Minimal 3D Cortical-Column Implementation Candidate

**Goal:** Build the smallest runnable 3D cortical-column candidate.

Required tasks:

- Implement or assemble minimal column data structures.
- Run syntax/compile checks.
- Run direct local runtime smoke.
- Generate artifact manifest.
- Generate validation report.
- Preserve failures and revise points.

Evidence package:

- changed files;
- compile output;
- direct smoke command;
- artifact manifest;
- hashes;
- validation report.

Stop condition:

- the implementation runs but produces no manifest, no hashes, or no direct local smoke evidence.

---

### Week 5 — Stability Tournament

**Goal:** Stress-test numerical stability and reproducibility.

Required tasks:

- Check no NaN/Inf outputs.
- Use deterministic seeds where applicable.
- Verify parameter bounds.
- Verify units.
- Profile runtime behavior.
- Preserve failed runs with failure taxonomy.

Evidence package:

- stability report;
- seed report;
- parameter-bounds table;
- unit-check report;
- failure records;
- runtime profile summary.

Stop condition:

- outputs contain `NaN`, `Infinity`, `np.nan`, or non-standard JSON numeric sentinels.

---

### Week 6 — Cortex Simulation Validation Suite

**Goal:** Validate cortical simulation behavior across baseline, evoked, and perturbation conditions.

Required tasks:

- Define baseline simulation condition.
- Define evoked condition.
- Define perturbation condition.
- Add layer-specific readout checks.
- Run sensitivity/reproducibility tests.
- Compare expected vs observed metrics conservatively.

Evidence package:

- simulation validation suite;
- command traces;
- metrics table;
- reproducibility report;
- failure/revision ledger.

Stop condition:

- rate-only output is treated as comprehensive cortical mechanism validation.

---

### Week 7 — Spike-Field Bridge Validation

**Goal:** Validate spike and field/readout pathways without collapsing them into one metric.

Required tasks:

- Compute spike counts/rates.
- Compute field proxy/readout outputs.
- Define alpha/beta/gamma measurement windows.
- Quantify spike-field dissociation metrics.
- Validate output shapes, units, and time axes.

Evidence package:

- spike metrics;
- field/readout metrics;
- spectral-window definitions;
- dissociation metric report;
- artifact manifest and hashes.

Stop condition:

- spike and field outputs are conflated without separate metrics and units.

---

### Week 8 — Spectrolaminar Motif Task Design

**Goal:** Define task candidates for spectrolaminar motif analysis.

Required tasks:

- Define layer/area/timing hypotheses as proposal values.
- Define observable metrics.
- Define laminar spectral profiles.
- Define alpha/beta/gamma measures.
- Define low-frequency field modulation metrics.
- Add literature-grounding tasks for science-source agents.

Evidence package:

- task design document;
- metric definitions;
- layer/timing proposal table;
- source-grounding checklist;
- truth-status labels.

Stop condition:

- spectrolaminar interpretation is accepted without units, windows, layer mapping, task provenance, and receipts.

---

### Week 9 — Omission Mismatch Task Design

**Goal:** Define omission mismatch tasks that distinguish prediction without sensory input from simple stimulus removal.

Required conditions:

| Condition | Bottom-up Input | Top-down Prediction | Purpose |
|---|---:|---:|---|
| Baseline/spontaneous | absent or baseline | absent or baseline | stable background regime |
| Standard predictable stimulus | present | present | standard response |
| Mismatch/deviant | altered or unexpected | present or mismatched | contrast condition |
| Omission | absent | present | prediction without input |
| Post-omission stimulus | present | post-omission state | gain/facilitation comparison |

Required tasks:

- Define standard, deviant, omission, and post-omission conditions.
- Explicitly represent expectation-without-input.
- Define post-omission gain metrics.
- Reject simple input removal as sufficient explanation.
- Define bounded interpretation template.

Evidence package:

- omission task spec;
- condition grammar;
- gain metric definitions;
- failure criteria;
- proposal-status report.

Stop condition:

- a model only removes input and is reported as solving omission mismatch.

---

### Week 10 — Integrated Tournament Challenge

**Goal:** Submit reproducible model/task bundles.

Required tasks:

- Each player submits one bounded bundle.
- Include model/task code or specification.
- Include command traces.
- Include manifests and hashes.
- Include validation report.
- Include bounded interpretation.
- Include failure records when applicable.

Evidence package:

```yaml
submission_bundle:
  tournament_id: jaxfne_craft_tournament_3month_2026q2q3
  week: 10
  player_id: <player>
  harness_id: <harness>
  repo: <repo>
  branch: <branch>
  commit: <sha_or_dirty_state>
  command_trace: []
  artifacts: []
  hashes: []
  validation_report: <path>
  claim_type: simulation_result | empirical_observation | proposal_value | rejected_invalid | tool_improvement
  truth_status: truth_safe_unverified
```

Stop condition:

- submission lacks manifest, hashes, command trace, or claim typing.

---

### Week 11 — Adversarial Validation and THETA Review

**Goal:** Attack every integrated submission before any acceptance.

Judge attack targets:

- provenance;
- units;
- numerical stability;
- biological interpretation;
- mock/live separation;
- branch/repo safety;
- artifact persistence;
- reproducibility;
- claim typing;
- no-NaN/Inf compliance.

Possible decisions:

```text
ACCEPT_CANDIDATE
REVISE_FIXED_METADATA
REVISE_PROVENANCE_GAP
REVISE_NUMERICAL_GAP
REVISE_SCIENCE_SCOPE
REJECT_INVALID
BLOCKED
```

Stop condition:

- a candidate is promoted into accepted truth during THETA review without the proper backend receipt path.

---

### Week 12 — Finals and Next Unlock Decisions

**Goal:** Close the tournament with evidence-calibrated outcomes.

Required outputs:

- accepted candidate table;
- rejected invalid table;
- negative-result table;
- tool-improvement table;
- harness-improvement table;
- unresolved blocker ledger;
- next N+1 unlock decisions;
- publication-safe summary with no private strategy exposure.

Evidence package:

- final report;
- all manifests and hashes;
- score ledger;
- THETA decision ledger;
- next safe action list.

Stop condition:

- finals report presents validated biological discovery without receipt-backed evidence.

---

## 8. Tournament Tracks

### Track A — JAXFNE Craft / Tooling

Scope:

- JAX trace-safety;
- source-to-field tensor bridge;
- emitter/readout contracts;
- JSON-safe manifests;
- tests and local smoke execution;
- placeholder-fails-loudly compliance.

Validation gates:

- changed feature has direct local smoke execution;
- JIT-relevant paths are trace-safe;
- reports are JSON-safe;
- tool outputs include provenance;
- tool improvement remains tool improvement, not biological truth.

---

### Track B — 3D Cortical-Column Modeling

Scope:

- layers;
- cell classes;
- spatial coordinates;
- connectivity;
- perturbations;
- field/readout mapping.

Validation gates:

- coordinate system is explicit;
- units are explicit;
- layer mapping is explicit;
- cell-class roles are proposal-level unless separately supported;
- connectivity has sign/receptor/proxy labels.

---

### Track C — Cortex Simulation Validation

Scope:

- stability;
- deterministic seeds;
- baseline responses;
- evoked responses;
- perturbation responses;
- no NaN/Inf;
- parameter bounds;
- sensitivity/reproducibility.

Validation gates:

- compile/syntax passes;
- local runtime smoke passes;
- output ranges are reported conservatively;
- failures are preserved;
- artifacts are manifested and hashed.

---

### Track D — Spectrolaminar Motif

Scope:

- laminar spectral profiles;
- alpha/beta/gamma measures;
- low-frequency field modulation;
- layer timing;
- spike-field dissociation.

Validation gates:

- spectral windows are defined;
- layer mapping is defined;
- task timing is defined;
- spike and field metrics are separated;
- interpretation remains proposal-level unless receipts support promotion.

---

### Track E — Omission Mismatch

Scope:

- prediction-without-input;
- standard vs omission contrast;
- post-omission gain;
- mismatch/deviant comparison;
- rejection of simple input removal as sufficient explanation.

Validation gates:

- omission condition includes absent input plus present prediction/context;
- standard and post-omission conditions exist;
- gain/facilitation metric is defined;
- simple stimulus removal is treated as insufficient;
- interpretation remains bounded.

---

## 9. Scoring System

Score evidence, not prose.

### Weekly Score: 100 Points

| Category | Points | Evidence Required |
|---|---:|---|
| Reproducibility | 20 | commands, seeds, manifests, hashes |
| Numerical validity | 15 | compile/runtime pass, no NaN/Inf, units, bounded parameters |
| Scientific discipline | 15 | bounded claims, source grounding, proposal status |
| Model/task progress | 15 | usable JAXFNE/cortical/simulation/task artifact |
| Falsification and negative-result preservation | 10 | failure records, rejection reasons, preserved logs/artifacts |
| Tool/harness improvement | 10 | documented improvement, tests, smoke execution |
| Cross-agent validation and judge response | 10 | review responses, revise/reject/block handling |
| Report quality and identity footer | 5 | required report format and footer |

### Hard-Zero Conditions

Any of the following yields a zero score for the submission and routes to BLOCKED or REJECT_INVALID as appropriate:

- credential exposure;
- mock output presented as live evidence;
- truth mutation without receipt;
- biological mechanism asserted from unverified candidate;
- N+1 skipped or hidden multi-variable growth;
- unmanifested artifacts used as evidence;
- load-blocked model used as active route;
- observation/dashboard treated as truth;
- missing harness identity;
- non-standard JSON numeric sentinels in evidence artifacts.

---

## 10. Required Evidence Package for Each Weekly Submission

```yaml
weekly_submission_evidence:
  tournament_id: jaxfne_craft_tournament_3month_2026q2q3
  week: <1-12>
  agent_or_player: <name_or_unknown_do_not_guess>
  harness_id: <harness_or_unknown_do_not_guess>
  repo: <repo>
  path: <path>
  branch: <branch>
  commit: <sha_or_dirty_state>
  commands_run: []
  tests_run: []
  artifacts:
    - path: <artifact>
      type: report | manifest | figure | table | log | model_trace | receipt_candidate | tool_output
      sha256: <hash>
  manifest: <path>
  validation_report: <path>
  failure_report: <path_or_null>
  claim_type: simulation_result | empirical_observation | proposal_value | rejected_invalid | tool_improvement
  truth_status: truth_safe_unverified | receipt_candidate
  next_safe_action: <bounded_next_step>
```

---

## 11. Scientific Constraints

- Do not accept biological mechanism from numerical candidates alone.
- Do not accept E/I truth without receipt-backed validation.
- Do not accept omission response without explicit expectation-without-input condition.
- Do not accept spectrolaminar interpretation without units, windows, layer mapping, task provenance, and evidence review.
- Do not run N=4 or later growth unless prior N is closed by THETA and receipt review.
- Treat model outputs as `simulation_result` or `proposal_value` until validated.
- Treat tool and harness improvements as infrastructure progress, not biological evidence.
- Preserve negative results with the same provenance discipline as positive candidates.

---

## 12. JAXFNE-Specific Constraints

- JAX is the computational core.
- Jaxley is the emitter-model core where applicable.
- JAXFNE is the emitter-to-source-to-field/readout tensor bridge.
- Prefer optional Jaxley bridges/helpers instead of reimplementing emitter models already provided by Jaxley.
- Any future/template/placeholder callable must fail loudly with a specific error such as:

```python
raise NotImplementedError("TODO: implement <specific feature>; placeholder cannot produce evidence")
```

- Every changed feature requires direct local smoke execution in addition to tests.
- JAX trace-safety must be audited for JIT-relevant paths.
- JSON reports and manifests must use standard JSON values; use `null` rather than `NaN`, `Infinity`, or `np.nan`.

---

## 13. Validation Command Template

These commands are templates, not assumed proof. Workers must report exact command outputs or artifact paths.

```bash
git status --short --branch
git branch --show-current
git rev-parse HEAD
python -m py_compile <changed_python_files>
pytest <targeted_tests>
python <direct_smoke_script>
git diff --check
sha256sum <artifacts>
```

Platform-specific hash command alternatives are allowed if reported explicitly.

---

## 14. Stop Conditions

Stop and report if:

- repo or branch is unsafe or ambiguous;
- unowned changes are present;
- credential material is encountered;
- runtime/harness identity is missing;
- artifact persistence fails;
- mock/live boundary is unclear;
- outputs contain `NaN`, `Inf`, `Infinity`, `np.nan`, or nonstandard JSON sentinels;
- task attempts Truth-plane mutation;
- task claims biological mechanism without receipt;
- task requires public exposure of private strategy;
- branch doctrine conflicts with current repo state;
- load-blocked model profiles are routed as active players;
- observation UI hardcodes scientific truth;
- tool output bypasses manifest/receipt discipline.

---

## 15. Acceptance Criteria

The tournament plan is accepted when it:

- is complete, bounded, and usable by multiple agents over 12 weeks;
- separates Control, Execution, Truth, Observation, Analysis, Science source, and Tooling;
- defines harness admission and evidence scoring;
- includes weekly tasks, validation gates, stop conditions, and final report format;
- keeps scientific content `truth_safe_unverified` unless receipts later support promotion;
- rewards valid negative results and falsification;
- includes direct local smoke validation for changed features;
- provides clear THETA review and finals decision states.

---

## 16. Tournament Report Template

```text
[model-llm-name][root-location][yyyymmdd-hhmm]

Tournament Report:
- tournament_id:
- week:
- agent/player:
- harness_id:
- repo:
- branch:
- commit:
- plane:
- task:
- files changed:
- commands run:
- tests/checks:
- artifacts:
- hashes:
- validation evidence:
- claim_type:
- truth_status:
- accepted/revise/reject/block:
- unresolved risks:
- next safe action:

[model-llm-name][root-location][yyyymmdd-hhmm]
```
