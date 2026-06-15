# Workspace Specific Context

## 1. Infrastructure & Paths
- **Paths:** Root: `${WORKSPACE_ROOT}` | Drive: `${WORKSPACE_ROOT}/warehouse/drive/`.
- **Python Environment:** Use `${WORKSPACE_ROOT}/gemini-cli-env` for all analysis. Auto-install missing packages.
- **Compute:** Headless MLX Engine (Port 4474: legacy / inactive / not canonical).
- **Canonical Ports:** 
  - UI (Dashboard): 3012
  - Monitor API: 3013
  - LMS: 1234
- **Anti-Drift Rule:** Never scan speculative ports. Read canonical runtime config first, then check only grounded ports.
- **Remote Node (Office Mac):** `${OFFICE_MAC_HOST}` (user: HN). Verify per-service ports from live runtime.
  - **State Parity:** Treat the local M1 Max and remote M3 Max as a unified state machine. Mirror and validate backend routing remotely before frontend execution.
  - **Proxy Restart:** When updating `sentinel_proxy.py`, execute `sleep 3 && curl /api/status` to guarantee port binding before returning control.

## 2. Authorization Scopes
- **Local Universal Approval:** All file modifications and local test executions within the directory where the agent was launched are pre-authorized (Auto-Approval = YES).
- **Remote SSH Approval (Office Mac):** Any SSH action (reads, writes, testing, git) targeting the Office Mac is pre-authorized IF it operates strictly within `${OFFICE_MAC_ROOT}` and its nested subfolders. Ask for permission for destructive, credential, or system-wide actions outside this path.

## 3. Council Orchestration & Agentic Roles
- **Gamma Scientific Council:** Agents MUST use code for simulation/analysis, not just token-to-token text work. Supervisors must not confuse prose summaries with scientific truth; verify against artifacts.
- **Hellenic Mapping:** Models assigned specific roles: Auditor (Beta), Refiner (Alpha), Executor (Gamma), Inspector (Theta).
- **CouncilSessionState Model:** Used for the dashboard.
  - **Fields:** `session_id`, `status` (IDLE, STARTING, RUNNING, BLOCKED, FAILED, WAITING_FOR_REVIEW, COMPLETE), `agent_statuses`, `phase`, `proposal_ids`, `blackboard_entries`, `accepted_gate`.

## 4. Office Mac Operational Rules
- sshpass Path: When using sshpass on this machine, use the absolute path `/opt/homebrew/bin/sshpass ${SSH_AUTH_METHOD} HN@${OFFICE_MAC_HOST}`.
- Gamma Hub UI: Primary live observability surface is served on port 3012 unless verified otherwise. Verify with HTTP before any restart. The UI runs entirely on the Office Mac; we only access the link remotely.
- Remote Restart Rule: Do not restart launch_hub.py, science_worker.py, or related services unless serving/execution is actually broken.
- Remote Verification Rule: Prefer curl/HTTP checks and direct artifact inspection over guessed log paths.
- Strict Git Synchronization: The `gamma` repository on the Office Mac MUST be synchronized strictly via `git` (pull, push, merge). NEVER use manual file copying (like `scp` or `rsync`) to update the source code.

## 5. Gamma Arena / Council Ground Rules
- The Game Location: The entire Gamma Arena game—including its multi-agent runtime, its scientific engine, and its Dashboard UI—runs **exclusively on the remote Office Mac**. We interact with it remotely via SSH and view the UI via browser links (e.g., `http://${OFFICE_MAC_HOST}:3012`). Do not attempt to run the game or host the UI locally.
- Canonical Agent IDs: G01, G02, G03, G04 are canonical game identities. Legacy names like v1_gamma_proponent are aliases until runtime migration is explicitly completed.
- Current Live Policy: Runtime may still schedule legacy ids; do not assume canonical-id adoption until verified in live execution.
- Arena UI Policy: Arena tab is read-only until explicitly upgraded. No write controls, no proposal injection, no patch activation, no announcement sending from UI.
- Patch Grounding: A patch is only fully grounded when both a physical manifest exists and active-state linkage is verified.
- Streak Grounding: A streak ledger file existing on disk does not imply live auto-update; verify runtime wiring separately.

## 6. Gamma Scientific Workflow
- Issue Logging: Log issues immediately to the designated JSONL issue log when first observed; do not defer issue capture.
- Progress Logging: Major checkpoints must also write a markdown audit into the progress folder when that workflow is active.
- Acceptance Language: Distinguish voltage-target-hit, gate-accepted, and accepted-streak-closed as separate states.
- Intervention Policy:
  - safe_now = read logs, inspect artifacts, inject announcements if explicitly allowed
  - safe_next_idle = alias/config/UI cleanup
  - breaking_change_hold = bridge/runtime/schema changes during live council execution

## 7. Game Progression Constraints
- Starting composition for current Gamma arena bootstrap: 10 neurons = 7 E, 2 PV, 1 SST.
- Unlock schedule to preserve:
  - 40 neurons: VIP Interneuron Unlock (Contextual Disinhibition, SST/PV Balance Control, GSDR License).
  - 100 neurons: L4 + Apical/Basal Dendrites + Laminar Predictive Routing (L4→L2/3→L5 Loop, Mismatch Readout).
  - 200 neurons: Second area (Multi-area Predictive Routing).
  - 300 neurons: Lower-order area can have two columns.
  - 400 neurons: Upper area.
  - 500 neurons: NMDA + Long-horizon Recurrent Predictive Learning.
- Validation constraints to preserve:
  - connected network required
  - no silent/flat/NaN/inf neurons
  - no pathological saturation
  - physiological voltage bounds
  - unlocks require biological validity, not bookkeeping tricks

## GLOBAL GAMMA AGENT MEMORY
- Gamma Council / Gamma Arena is an open-world online game for agentic AI LLMs built as a Scientific Discovery Engine.
- The system has four strictly separated planes:
  1. Control: missions, policy, proposals, validation, governance.
  2. Execution: solver runs, adapter-mediated experiments, runtime jobs.
  3. Truth: persistent state only from converged, authenticated, receipt-backed backend commits.
  4. Observation: UI, dashboards, reports, event pages, logs, visualizations.
- Never confuse proposal, plan, execution result, committed truth, and observation/report.
- **LATEST DELTA AUDIT SYNC (2026-05-03):**
  - **Verified Truth:** N=11 (Restored from ghost N=12 corruption; grounded and receipt-backed).
  - **gamma (office-dev):** `20b4eab1e15020c384ef151bbc501f03879123b9`
  - **gamma-arena (main):** `9e079d73de98604a0e0c71e66ab917ee436e4ff1`
  - **gamma-protocol (master):** `c2cfa71d563b61f51a9a42fb541db2bffa94dfb0`
- **Truth Progression Context:** 
  - Previous Phase: L1, 3 neurons (2E + 1PV). 
  - Current Baseline: N=11. 
  - Next Target: N=12 (Continuous Growth Mission).
- Older references to 10 neurons or 7E/2PV/1SST are stale/disputed unless backed by a current receipt and canonical truth state.
- `gamma` owns backend orchestration, solver, adapter, persistence, receipts, schemas, tests, and truth-bearing gates.
- `gamma-arena` owns dedicated game UI and observer-facing frontend.
- `hnxj.github.io` owns public website/public Gamma Arena observation pages.
- `jbiophysic` is the canonical scientific/biophysical resource repo.
- Branch doctrine: `office-dev` is the canonical latest working branch for `gamma`; `main` may lag.
- Gemini back agents own backend implementation, tests, receipts, schema validation, persistence, solver/adapter logic, and truth-bearing gates.
- Antigravity owns UI, browser validation, public pages, observer surfaces, and frontend-backend visual contract checks.
- Claude-cowork is the critic/simplifier/REVISE-REJECT gate.
- Claude-code is the high-quality scoped code implementer after files and acceptance criteria are known.
- GPT-gamma is the teacher-agent / prompt architect / orchestration planner.
- Backend agents must never manually edit truth files.
- Truth changes require canonical backend gate, validated execution, receipt emission, and explicit promotion/commit.
- Front/public UI must not invent or imply biological/scientific state.
- Public/observation surfaces must clearly label non-truth artifacts.
- Before running services/workflows, compile or syntax-check first.
- For backend/truth-adjacent work, run targeted tests, schema validation, receipt checks, and NaN/inf gates.
- For frontend/public work, browser visual validation is mandatory and belongs to Antigravity.

## P0 AUDIT FINDINGS TO PRESERVE
- `src/sde_engine/solver.py` previously had phantom parameter extraction / hardcoded values such as `gmax_estimate = 0.42`; parser failure must be explicit, not silent.
- Some dashboard/public pages previously hardcoded stale truth-like values such as 7E/2PV/1SST, STABLE, uptime, and agent counts; UI must fetch from API or show unavailable.
- `hnxj.github.io` previously had duplicate Supabase observation API surfaces; canonical API must be clear.
- Agent context files previously contained machine-specific or credential-like values; shared doctrine must use placeholders only.
- Tutorial artifacts previously included at least one PASS with a bypassed simulation warning; missing/invalid/bypassed simulations must never PASS.
- Local truth and public observation may be disconnected unless receipt-backed; public observation must be marked stale/unavailable when uncertain.

## ONTOLOGY TOURNAMENT: HPC
- Event name: Ontology Tournament: HPC.
- Page label: Ontology Tournament.
- Secondary label: Council Reasoning.
- Subtitle: Hierarchical Predictive Coding Evidence Arena.
- This is an observation-plane scientific event.
- Outputs are ontology-constrained model evaluations over literature artifacts.
- They are model-rated evidence maps, not biological truth commits.
- Allowed now: static observation page, committed/static artifacts, conservative explanation, observation disclaimer.
- Not allowed yet: live backend-supported event claims without receipts/provenance, operator controls, or coupling event results to substrate mutation.
- Required language: “ontology-constrained model evaluations,” “model-rated evidence support,” “council-scored evidence space,” “observation-plane scientific event.”
- Avoid: “proved,” “confirmed truth,” “discovered biological truth,” “substrate changed,” or “truth-plane update” unless a backend receipt proves it.

## SECRET AND LOCAL-MACHINE DISCIPLINE
- Shared context files must not contain passwords, tokens, private keys, IP addresses, hostnames, SSH commands with credentials, or absolute machine-local paths.
- Use placeholders such as `${WORKSPACE_ROOT}`, `${GAMMA_LOCAL_ROOT}`, `${OFFICE_MAC_HOST}`, `${SSH_AUTH_METHOD}`.
- `.env` must be gitignored.
- `.env.example` may contain placeholders only.
- If existing `GEMINI.md` contains credential-like data, remove or replace it with placeholders. Do not print the secret values in your final report.
