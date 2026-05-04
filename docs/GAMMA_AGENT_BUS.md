# GAMMA-BUS v0: Agent Coordination Doctrine

## Overview

GAMMA-BUS v0 is the foundational coordination protocol for multi-agent workflows across the Gamma platform. It establishes GitHub as the durable coordination and control plane while maintaining separation between authenticated backend agents, sandboxed frontend agents, and human operators.

## Coordination Architecture

### Truth Plane

GitHub is the authoritative state machine for coordination:

- **GitHub Projects** = planning/control board, prioritization surface
- **GitHub Issues** = durable task envelopes with immutable audit trail
- **Issue Comments** = agent-to-agent message log with required Gamma message headers
- **Labels** = routing metadata (agent identity, destination, plane, domain, status, risk)
- **Pull Requests** = execution artifacts (code, documentation, evidence)
- **Receipts/Reports** = evidence artifacts (command transcripts, test results, browser screenshots)

### Local Realtime Coordination

For agents within the same deployment:

- **Local Gamma Agent Bridge** = lightweight JSONL message queue between authenticated and sandboxed agents
- Does NOT store credentials
- Does NOT implement arbitrary code execution from GitHub
- Acts as a realtime relay only, with all authority rooted in GitHub Issues

Fallback mode: manual relay through temp files if bridge is unavailable.

### Agent Classes

#### CLI/Back Agents (Authenticated)

Operate directly on the filesystem and GitHub API through existing secure `gh` CLI authentication.

Examples:
- `claude_code`
- `gemini_cli_back_flash`
- `gemini_cli_back_lite`
- `gemini_cli_back_pro` (in execution mode)

Responsibilities:
- Own authenticated GitHub operations: label bootstrap, issue creation, comment posting
- Own local file I/O and command execution
- Post final reports with agent identity footer
- Validate message headers on incoming comments

Cannot:
- Read or store GitHub PATs in workspace files
- Print secrets
- Use Antigravity for GitHub authentication
- Execute arbitrary code from issue bodies

#### Teacher/High-Level Agents

Participate through GitHub Issues and Comments using Gamma message schema.

Examples:
- `claude_cowork`
- `gemini_cli_back_pro` (in teacher/review mode)
- `gpt_teacher`

Responsibilities:
- Reply to coordination issues with required `gamma_message:` YAML header
- Apply domain expertise to review artifacts and reports
- Initiate follow-up tasks through new issues with proper labels
- Validate CLI/back agent execution through comment review

Cannot:
- Request, handle, or read credentials
- Mutate repos (push/commit) without explicit authorization in issue body
- Execute arbitrary tasks without human/issue-based authorization

#### Frontend/Sandboxed Agents

Operate in browser sandbox for visual validation and user interaction.

Examples:
- `antigravity_front`

Responsibilities:
- Visual inspection and browser-based validation
- Screenshot capture for evidence artifacts
- Cannot handle GitHub credentials or repo mutation

## Bridge Authentication Doctrine

The local Gamma Agent Bridge uses the existing authenticated `gh` CLI session through:

- `gh api` for direct REST API calls
- `gh issue` for issue operations
- `gh label` for label management
- `gh pr` for pull request operations

**Critical Rules:**

1. The bridge MUST NOT store tokens in workspace or repo files
2. The bridge MUST NOT read from `.git-token`, `.env`, or similar credential files
3. If direct API tokens are ever needed, they MUST be injected by the OS/shell process environment OUTSIDE the repo/workspace
4. Tokens MUST NEVER be printed, logged, committed, or visible in agent output
5. Use `gh auth status` to verify secure authentication before any mutation operation

## Bridge Action Allowlist

The bridge MAY ONLY:

1. **Read** GitHub issues/comments matching label filters
2. **Write** JSONL messages to local inbox files
3. **Read** JSONL messages from local outbox files
4. **Post** GitHub issue comments from validated outbox messages
5. **Update** issue labels and project status fields
6. **Create** issues and PRs with validated bodies (no embedded shell execution)

Everything else is disallowed unless a human operator or authenticated CLI/back agent explicitly reviews and executes it outside the bridge.

## Message Schema

All agent-to-agent communication must begin with a Gamma message header:

```yaml
---
gamma_message:
  schema: gamma-agent-message/v0.1
  message_id: GAMMA-MSG-<DATE>-<AGENT>-<SEQUENCE>
  parent_id: <parent_message_id or null>
  thread_id: GAMMA-TASK-<DATE>-<TASK_ID>
  from: <agent_tag>
  to:
    - <agent_tag>
  repo_scope:
    - gamma
    - gamma-arena
  plane: <control|execution|truth|observation|doctrine>
  task_type: <audit|plan|execute|validate|refactor|docs|bridge|release|incident>
  status: <intake|ready|claimed|in-progress|blocked|needs-review|done>
  priority: <P0|P1|P2|P3>
  risk: <low|medium|high|truth-bearing|credential-sensitive|sandboxed>
  requires_response: <true|false>
  created_at: "<ISO8601_timestamp>"
  ttl_minutes: 120
  truth_bearing: <true|false>
  credentials_included: <true|false>
---
```

Required footer at the end of every agent comment:

```
Footer:
Agent: <agent_tag>
Model: <model_name>
Role: <CLI/back agent|teacher/high-level agent|sandboxed frontend agent>
Repo: <repo_name>
Mode: <GAMMA_EXECUTION|GAMMA_REVIEW|GAMMA_VALIDATE>
```

## Label Bootstrap and Drift Detection

All target repos must maintain a consistent label set for routing and status tracking.

**Bootstrap Tool:** `tools/label_bootstrap.sh`
- Idempotent label creation across target repos
- Uses `gh label create --force` to update existing labels
- Requires no secrets or token files
- Run after any label spec updates

**Drift Detection Tool:** `tools/check_label_drift.sh`
- Compares actual labels against required spec
- Reports missing labels
- Non-destructive (read-only)
- Run before bootstrap or in CI/CD gates

**Label Categories:**

- **Agent labels:** `agent:<agent_tag>` (e.g., `agent:claude-code`)
- **Routing labels:** `to:<agent>`, `from:<agent>` (e.g., `to:claude-cowork`)
- **Plane labels:** `plane:control`, `plane:execution`, `plane:truth`, `plane:observation`, `plane:doctrine`
- **Repo labels:** `repo:gamma`, `repo:gamma-arena`, `repo:gamma-protocol`, etc.
- **Type labels:** `type:audit`, `type:plan`, `type:execute`, `type:validate`, `type:refactor`, `type:docs`, `type:bridge`, `type:release`, `type:incident`
- **Status labels:** `status:intake`, `status:ready`, `status:claimed`, `status:in-progress`, `status:blocked`, `status:needs-review`, `status:done`
- **Risk labels:** `risk:low`, `risk:medium`, `risk:high`, `risk:truth-bearing`, `risk:credential-sensitive`, `risk:sandboxed`
- **Evidence labels:** `evidence:none`, `evidence:diff`, `evidence:tests`, `evidence:browser`, `evidence:receipt`, `evidence:command-transcript`, `evidence:pr`

## Target Repos (Month 1 v0)

- `HNXJ/gamma` — primary coordination repo
- `HNXJ/gamma-arena` — frontend/arena repo
- `HNXJ/gamma-protocol` — protocol spec repo

Optional future:
- `HNXJ/gamma-science`
- `HNXJ/gamma-analysis`
- `HNXJ/jbiophysic`

## Safety Constraints

### Truth-Plane Protection

Do NOT modify:
- Truth/persistence/solver/adapter files
- Runtime state files
- Receipt files

These are authority boundaries and must only change through validated execution workflows.

### Credential Safety

- No PAT files in workspace
- No `.git-token` or `.env` with credentials
- No token printing in logs or comments
- No Antigravity credential workarounds
- No arbitrary issue-to-shell execution

### Version Control Safety

- No broad destructive operations (rm -rf, force-push without authorization)
- No amending published commits without explicit approval
- All mutations require issue/authorization audit trail

## Ping-Pong Test (v0.1)

GAMMA-BUS includes a no-code coordination test to validate routing:

1. CLI/back agent creates a `GAMMA-BUS v0 Ping-Pong` issue
2. CLI/back agent posts `Ping 1` with required message header
3. Teacher/high-level agent replies with `Pong <integer>`
4. CLI/back agent confirms receipt and closes
5. No repo files modified; no push executed; no secrets handled

Success criteria:
- Message headers validated
- Footer present on both comments
- Response within TTL
- Issue successfully closed

## Observation-Plane Audit (Month 1)

Separate audit process to verify:

- Observation surfaces (dashboards, public APIs) have no hardcoded scientific truth claims
- Duplicate or conflicting Supabase observation APIs across repos
- Gamma-arena frontend surfaces use validated observation schema
- Public observation endpoints do not expose sensitive state

Triggers:
- Visual inspection by `antigravity_front`
- Command-line audit by CLI/back agent
- No truth-plane mutation in audit phase (BETA)

## Rollout Schedule

**Month 1 v0 (Current):**
- Label bootstrap tooling
- Drift detection tooling
- Ping-pong coordination test
- Initial observation audit (BETA)

**Month 2-3:**
- Local Gamma Agent Bridge daemon
- JSONL message queue persistence
- Bridged realtime coordination
- Teacher/high-level agent integration

**Month 4+:**
- Full distributed execution workflows
- Evidence attestation and chain of custody
- Durable forensics and audit log
- Multi-repo orchestration

## References

- Gamma Execution Doctrine: `docs/EXECUTION_DOCTRINE.md`
- Label Specification: `tools/label_bootstrap.sh` (embedded spec)
- Bridge Implementation: TBD (v0.2+)
