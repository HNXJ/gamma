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

## 4. Office Mac Operational Rules
- SSH Usage: Use the pinned-key SSH doctrine defined in Section 8. Never use plaintext passwords or plain SSH commands.
- Gamma Hub UI: Primary live observability surface is served on port 3012 unless verified otherwise. Verify with HTTP before any restart. The UI runs entirely on the Office Mac; we only access the link remotely.
- Remote Restart Rule: Do not restart launch_hub.py, science_worker.py, or related services unless serving/execution is actually broken.
- Remote Verification Rule: Prefer curl/HTTP checks and direct artifact inspection over guessed log paths.
- Strict Git Synchronization: The `gamma` repository on the Office Mac MUST be synchronized strictly via `git` (pull, push, merge). NEVER use manual file copying (like `scp` or `rsync`) to update the source code.

## 5. Gamma Arena / Council Ground Rules
- The Game Location: The entire Gamma Arena game—including its multi-agent runtime, its scientific engine, and its Dashboard UI—runs **exclusively on the remote Office Mac**. We interact with it remotely via SSH and view the UI via browser links (e.g., `http://100.69.184.42:3012`). Do not attempt to run the game or host the UI locally.
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

## 8. Gamma SSH / Office Mac Doctrine
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


## GAMMA-BUS Coordination Doctrine

Gamma Labyrinth uses a separated-but-synchronized coordination architecture:

1. **ChatGPT/Hamm orchestration chat**
   - Teacher/orchestrator cockpit.
   - Used for routing, synthesis, prompt generation, DELTA reconciliation, and final next-action decisions.
   - Not the durable execution ledger by itself.

2. **GitHub issue in \`gamma-labyrinth\`**
   - Standing GAMMA-BUS Coordination Thread.
   - Single durable cross-agent coordination thread / active agent ledger.
   - No secrets, no executable payloads, no unreceipted scientific truth.
   - Used for short cross-agent status, task links, blockers, handoffs, and final report links.

3. **GitHub Project \`gamma\`**
   - Control-plane board/status/task table.
   - Tracks issues, labels, status, routing, ownership, and evidence.
   - Not scientific Truth-plane state unless backed by receipts.

4. **Separate task issues**
   - Durable work envelopes for specific tasks.
   - Each task issue should specify repo, branch, plane, agent, scope, forbidden scope, evidence required, stop conditions, and final report format.

5. **Separate worker chats**
   - Agent-specific execution channels.
   - Windows Antigravity: front/UI/browser validation.
   - Gemini CLI: backend/runtime/git/terminal work.
   - Claude/Cowork: doctrine, audit, DELTA reconciliation, and high-level review.
   - Keep worker chats separate to avoid context contamination.

6. **Google Drive**
   - Artifact storage only: screenshots, PDFs, exported reports, large files.
   - Not the coordination ledger or source of task truth.

### Required agent behavior:
**Before work:**
- Check the relevant task issue and, when available, the GAMMA-BUS Coordination Thread.
- Verify repo, branch, plane, scope, and task ownership.
- Assume parallel agents may be active.

**During work:**
- Stay within assigned scope.
- Do not apply fixes in one repo/agent context that could conflict with another agent’s sensitive pending work.
- If another agent/repo/human dependency is needed, create or update a GitHub issue rather than relying only on chat.

**After work:**
Report with:
- agent/model
- repo/branch
- plane
- files changed
- commands run
- tests/validation
- commit/PR/artifact/screenshot/receipt links
- unresolved risks
- next single action
- footer with agent label/model/role/plane/truth_mode/date

### Truth and security constraints:
- No secrets in issues, memory files, prompts, or reports.
- No biological/scientific truth claims without Truth-plane receipts.
- Observation pages are not truth.
- GitHub Project state is task/control state, not scientific truth.
- Use \`truth_mode: truth_safe_unverified\` when no current receipt exists.
