# Workspace Specific Context

## 1. Infrastructure & Paths
- **Paths:** Root: `/Users/hamednejat/workspace/` | Drive: `/Users/hamednejat/workspace/warehouse/drive/`.
- **Python Environment:** Use `/Users/hamednejat/workspace/gemini-cli-env` for all analysis. Auto-install missing packages.
- **Compute:** GLLM Control Panel (`localhost:3005`). Headless MLX Engine (`port 4474`).
- **Remote Node (Office Mac):** `100.69.184.42` (user: HN). Verify per-service ports from live runtime; Gamma Hub UI commonly uses 3012.
  - **State Parity:** Treat the local M1 Max and remote M3 Max as a unified state machine. Mirror and validate backend routing remotely before frontend execution.
  - **Proxy Restart:** When updating `sentinel_proxy.py`, execute `sleep 3 && curl /api/status` to guarantee port binding before returning control.

## 2. Authorization Scopes
- **Local Universal Approval:** All file modifications and local test executions within the directory where the agent was launched are pre-authorized (Auto-Approval = YES).
- **Remote SSH Approval (Office Mac):** Any SSH action (reads, writes, testing, git) targeting the Office Mac is pre-authorized IF it operates strictly within `/Users/HN/MLLM/` and its nested subfolders. Ask for permission for destructive, credential, or system-wide actions outside this path.

## 3. Council Orchestration & Agentic Roles
- **Gamma Scientific Council:** Agents MUST use code for simulation/analysis, not just token-to-token text work. Supervisors must not confuse prose summaries with scientific truth; verify against artifacts.
- **Hellenic Mapping:** Models assigned specific roles: Auditor (Beta), Refiner (Alpha), Executor (Gamma), Inspector (Theta).
- **CouncilSessionState Model:** Used for the dashboard.
  - **Fields:** `session_id`, `status` (IDLE, STARTING, RUNNING, BLOCKED, FAILED, WAITING_FOR_REVIEW, COMPLETE), `agent_statuses`, `phase`, `proposal_ids`, `blackboard_entries`, `accepted_gate`.

## 4. Instructional Chains / Teacher-Student Runtime Conditioning
- **runtime_teacher_prompting:** Claude/Gemini prompts, continuity banners, examples, rubrics, or judge feedback shape Gemma behavior during a session.
  - Evidence: prompt files, request JSON, session manifests, transcripts, judge outputs, artifact hashes.
  - Truth status: behavioral/session evidence only; not model-origin truth.
- **weight_or_adapter_distillation:** A model checkpoint, adapter, LoRA/DoRA/FedLoRA artifact, or named derivative was trained from teacher outputs or teacher-guided data.
  - Evidence: model card, training manifest, adapter metadata, checkpoint provenance, artifact hash.
  - Truth status: model-provenance evidence if verified; requires specific provenance artifacts.
- **unknown_or_name_only_claim:** A model ID or filename suggests lineage, but no provenance artifact has been verified.
  - Truth status: truth_safe_unverified.
- **Current Status:** The 8 Gemma slots are treated as `runtime_teacher_prompting` unless verified provenance artifacts exist. Teacher-student outputs are proposal/session artifacts, not Truth-plane state. Baseline behavior auditing is recommended but not a blanket gate for all proposal-only runs.

## 5. Office Mac Operational Rules
- SSH Usage: Use the pinned-key SSH doctrine defined in Section 9. Never use plaintext passwords or plain SSH commands.
- Gamma Hub UI: Primary live observability surface is served on port 3012 unless verified otherwise. Verify with HTTP before any restart.
- Remote Restart Rule: Do not restart launch_hub.py, science_worker.py, or related services unless serving/execution is actually broken.
- Remote Verification Rule: Prefer curl/HTTP checks and direct artifact inspection over guessed log paths.
- Strict Git Synchronization: The `gamma` repository on the Office Mac MUST be synchronized strictly via `git` (pull, push, merge). NEVER use manual file copying (like `scp` or `rsync`) to update the source code.

## 6. Gamma Arena / Council Ground Rules
- Gamma Labyrinth runtime surfaces are distributed. Windows is the primary local workspace/runtime/front-agent machine for local hosts, UI checks, and Antigravity/front validation. Office Mac is primarily a backend local-LLM/model handler for larger player models and LM Studio/OpenAI-compatible endpoints when applicable. Windows LMS is a small guard/judge/receptionist/debug layer unless explicitly changed. Verify host, route, and runtime state before claiming any service is live.
- Canonical Agent IDs: G01, G02, G03, G04 are canonical game identities. Legacy names like v1_gamma_proponent are aliases until runtime migration is explicitly completed.
- Arena UI Policy: Arena tab is read-only until explicitly upgraded.
- Patch Grounding: A patch is only fully grounded when both a physical manifest exists and active-state linkage is verified.
- Streak Grounding: A streak ledger file existing on disk does not imply live auto-update; verify runtime wiring separately.

## 7. Gamma Scientific Workflow
- Issue Logging: Log issues immediately to the designated JSONL issue log when first observed; do not defer issue capture.
- Progress Logging: Major checkpoints must also write a markdown audit into the progress folder when that workflow is active.
- Acceptance Language: Distinguish `voltage-target-hit`, `gate-accepted`, and `accepted-streak-closed` as separate states.
- Intervention Policy:
  - safe_now = read logs, inspect artifacts, inject announcements if explicitly allowed
  - safe_next_idle = alias/config/UI cleanup
  - breaking_change_hold = bridge/runtime/schema changes during live council execution

## 8. Game Progression Constraints
- Historical/proposal scientific progression examples may appear in prior reports, but GEMINI.md is not a Truth-plane receipt. Active neuron count, cell composition, unlock schedule, accepted streak, or growth target must be loaded from current receipt-backed Truth-plane state. Without such receipt evidence, use `truth_mode: truth_safe_unverified` and `claim_type: proposal_value` or `historical_reported_context`.
- Validation constraints to preserve:
  - connected network required
  - no silent/flat/NaN/inf neurons
  - no pathological saturation
  - physiological voltage bounds
  - unlocks require biological validity, not bookkeeping tricks

## 9. Gamma SSH / Office Mac Doctrine
- Every durable report must begin and end with exactly:
  [model-llm-name][root-location][yyyymmdd-hhmm]
  Use verified values only; otherwise use `unknown_model_do_not_guess` or `unknown_root_do_not_guess`.
- Office Mac target is `HN@100.69.184.42`; world root is `/Users/HN/gamma-world`.
- Use only pinned-key SSH form:
  `ssh -o BatchMode=yes -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 HN@100.69.184.42 '<command>'`
- Never use plain `ssh HN@100.69.184.42` from agents.
- Never ask the user to run `ssh-add -D` or clear their SSH agent.
- The private key is passphrase-protected. The user’s interactive terminal can work after `ssh-add --apple-use-keychain ~/.ssh/id_ed25519`, but an agent subprocess may not inherit `SSH_AUTH_SOCK`.
- If `ssh-add -l` says `Could not open a connection to your authentication agent` or `env | grep SSH` shows no `SSH_AUTH_SOCK`, do not attempt repeated SSH recovery. Report `BLOCKED_AGENT_SSH_AUTH_SOCK_MISSING`.
- Before killing any local tunnel on port 8787, first test:
  `curl -sS --max-time 5 http://127.0.0.1:8787/health`
  If it works, do not kill the tunnel.
- The local tunnel is dev-only:
  `127.0.0.1:8787 -> Office Mac 127.0.0.1:8787`.
- The hosted/Vercel architecture should not depend on this tunnel. Office Mac should push observation rows outward to a cloud observation relay/store; Vercel should read from cloud, not pull from Office Mac localhost.