# Canonical Agent Stack Spec

### 1. Purpose
This stack exists to make agent work: reliable under weaker models, fast under compressed context, hard to misconfigure, and grounded in code/config/runtime truth rather than stale memory.

The system should prefer: config over literals, audit over assumption, preflight over late failure, structured events over raw logs, and extracted reusable skills over repeated rediscovery.

---

### 2. Core operating doctrine
Every major action must follow this order:
1. capability grounding
2. evidence grounding
3. preflight
4. execution or audit
5. structured result
6. extraction review

No agent should: guess ports, treat memory as runtime truth, treat readable status as writable control, mark placeholders as implemented, or claim “running” without runtime proof.

---

### 3. Canonical tools

#### 3.1 Mandatory CLI tools

`/capabilities-audit`
Reports:
* active mode
* available tools
* unavailable tools
* shell availability
* SSH availability
* write scope
* interpreter path
* policy tier
* workspace root
Purpose: prevent tool-surface mismatch before any audit or repair.

`/beta`
Read-only compact audit. Outputs strict JSON with evidence classes, confidence, blockers, drift, configured ports, startup readiness, and surface classification.

`/alpha`
Smallest local corrective repair after Beta proves the issue.

`/gamma`
Execution mode. Only valid after preflight passes.

`/theta`
Postmortem mode. Identifies first collapse point and separates proven from inferred causes.

#### 3.2 Specialized operational tools

`/startup-verify`
Runs preflight only. Does not launch a mission if blocked.

`/port-audit`
Finds all configured ports, literal port usage, service-role mapping, and drift.

`/model-audit`
Reports model key, resolved runtime name, model-loaded state, provider, and readiness blockers.

`/stream-audit`
Reports:
* schema present
* runtime emission present
* monitor consumption present
* UI surface present

`/inventory-audit`
Validates inventory layout, required files, schema integrity, and last stable artifact.

`/parity-audit`
Compares:
* memory
* config
* code
* remote runtime
* remote control surface

`/endpoint-discover`
Reads live HTML/JS and extracts real API routes instead of guessing them.

`/remote-diff`
Compares local and remote code/config/runtime when remote verification is possible.

---

### 4. Canonical code modules
These should exist as stable modules, not scattered logic.

`src/gamma_runtime/config.py`
Single source of truth for:
* `OFFICE_MAC_HOST`
* `LMS_PORT`
* `HUB_PORT`
* `DASHBOARD_PORT`
Also provides canonical URL builders.

`src/gamma_runtime/preflight.py`
Central fail-fast startup checks:
* correct interpreter / `.venv`
* required imports
* inventory existence
* configured port reachability
* model availability if inference is required
* failure_reason emission

`src/gamma_runtime/model_readiness.py`
Separates: HTTP reachable, model loaded, inference-ready.

`src/gamma_runtime/provenance.py`
Defines:
* `CouncilExecutionRecord`
* `CouncilStreamEvent`

`src/gamma_runtime/identity.py`
Resolves role-distinct runtime model names.

`src/gamma_runtime/inventory_schema.py`
Validates:
* `memory.md`
* `latest_state.json`
* `latest_input.json`
* `latest_output.json`
* `latest_judgment.json`
* `events.jsonl`

`src/gamma_runtime/audit_assertions.py`
Contains reusable truth assertions:
* placeholder not implemented
* config outranks memory
* readable runtime does not imply writable control
* startup success requires runtime proof

`src/gamma_runtime/surfaces.py`
Defines and classifies surfaces:
* memory surface
* config surface
* code surface
* runtime status surface
* control surface
* SSH surface
* model surface

---

### 5. Canonical skills

#### 5.1 Skills that should exist now

`evidence-surface-grounding`
Use whenever memory, config, code, HTTP runtime, or remote control surfaces are being compared.

`flash-agent-preflight`
Use before startup, restart, orchestration, or environment-sensitive execution.

`gamma-port-canonicalization`
Use whenever touching startup, networking, API, or backend files.

`startup-truth-criteria`
Use before claiming the game or service is “running.”

`runtime-surface-classification`
Use whenever a readable surface might be confused with a writable one.

`lms-model-readiness-gate`
Use before any inference-dependent execution.

`compact-audit-design`
Use when adding or changing compact audit fields.

`inventory-schema-discipline`
Use whenever agent inventory structure is created or modified.

`structured-event-bridge`
Use whenever front-facing telemetry or event streaming is changed.

`role-memory-task-layering`
Use whenever prompts or per-agent memory composition is changed.

`gamma-branch-parity-audit`
Use whenever local and remote states seem inconsistent.

#### 5.2 Canonical skill metadata
Every skill should carry:
* name
* class
* trigger_conditions
* purpose
* implementation_home
* enforcement_home
* documentation_home
* acceptance_tests
* anti_regression_hook
* blast_radius

Skill classes:
* code_module
* audit_doctrine
* cli_surface
* memory_policy
* lint_rule
* preflight_gate
* audit_assertion

---

### 6. Policy model
Policies should be more liberal inside trusted scope and strict outside it.

#### 6.1 Pre-authorized local scope
Inside `/Users/hamednejat/workspace/`, allow:
* read
* write
* replace
* shell
* git
* tests
* local scripts
* config edits
* skill activation

#### 6.2 Pre-authorized remote scope
Inside `/Users/HN/MLLM/` on the Office Mac, allow:
* SSH read/write/test/git
* curl
* log inspection
* service checks
* model/load checks
* config inspection
* startup verification

#### 6.3 Approval boundaries
Require approval only for:
* destructive actions outside scope
* credential changes
* system-wide package changes outside project venv
* broad destructive shell commands
* filesystem operations outside authorized roots

#### 6.4 Hard policy doctrine
* deny plan mode by default unless explicitly requested
* never guess ports if config exists
* never mark a placeholder as complete
* never claim runtime success without proof
* never treat memory as runtime truth
* never infer writable control from readable HTTP status

---

### 7. Memory policy
Memory should store durable invariants, not transient runtime state.

#### 7.1 Memory should contain
* stable repo paths
* stable authorization rules
* stable unlock schedule
* stable role definitions
* stable workflow doctrine
* stable tool/workspace conventions
* proven long-term project constraints

#### 7.2 Memory should not contain
* current mission target
* current active patch
* current live port assumptions
* current live branch/runtime assumptions
* ephemeral session IDs
* temporary failure states

#### 7.3 Canonical rule
Ports, progression state, and live runtime state must come from: config artifacts, compact audit, or live runtime surfaces, not memory files.

---

### 8. Prompt architecture
Role, memory, and task must remain separate.
Prompt assembly order:
1. role block
2. memory block
3. current world state / patch state
4. live task prompt

Role is stable identity.
Memory is durable personal state.
Task is current action.
Never merge role into long-term memory.

---

### 9. Inventory schema
Per-agent inventory root: `local/inventory/GXX/`

Required files:
* `memory.md`
* `latest_input.json`
* `latest_output.json`
* `latest_judgment.json`
* `latest_state.json`
* `events.jsonl`
* `player/`

#### 9.1 Semantics

`memory.md`
Durable long-term state: last stable approved artifact, last stable code filename, known good workflow, known bad failure modes, durable score/perk/item state if needed.

`latest_input.json`
Last exact turn input.

`latest_output.json`
Last exact turn output.

`latest_judgment.json`
Last judge result.

`latest_state.json`
Machine-readable current state.

`events.jsonl`
Append-only event timeline.

`player/`
Self-directed workspace.

---

### 10. Startup truth criteria
A process is not “running” just because a port is bound. A valid “running” claim requires:
1. preflight success
2. correct interpreter
3. required imports available
4. configured ports reachable
5. model availability confirmed if inference required
6. inventory structure present
7. status endpoint valid if applicable
8. at least one real orchestrator/runtime event beyond synthetic bootstrap

Synthetic inventory or startup events do not prove live orchestration.

---

### 11. Surface classification
Every audit must explicitly separate:
`local_memory_context`
`local_config_artifact`
`local_code_artifact`
`remote_http_runtime`
`remote_control_surface`
`ssh_surface`
`model_surface`

#### Rules
Memory never outranks config.
Config never implies live runtime.
Readable runtime does not imply writable control.
HTTP reachability does not imply model readiness.
Schema existence does not imply runtime emission.
Runtime emission does not imply monitor consumption.
Monitor consumption does not imply UI surface correctness.

---

### 12. Compact audit requirements
The compact audit must emit strict machine-readable output.

Minimum fields:
* timestamp
* environment
* configured_ports
* audit_roots
* local_memory_context
* local_config_artifact
* local_code_artifact
* remote_http_runtime
* remote_control_surface
* model_surface
* cross_surface_consistency
* literal_port_usage_findings
* parity_blockers
* evidence
* confidence

#### Required truth subfields

For streaming:
* `structured_stream_schema_present`
* `structured_stream_emission_present`
* `structured_stream_monitor_consumption_present`
* `structured_stream_ui_surface_present`

For runtime:
* `runtime_status_surface_grounded`
* `control_surface_grounded`
* `ssh_surface_grounded`

For startup:
* `preflight_ready`
* `failure_reason`
* `model_loaded`

For orchestration:
* `app_layer_dispatch_mode`
* `scheduler_capability_present`

---

### 13. Anti-regression rules
These must be enforced in code or audit, not only remembered.

Forbidden patterns:
* literal backend/service ports in runtime files
* placeholder comments in live endpoint handlers
* “RUNNING” log before preflight success
* synthetic events used as proof of agent life
* memory files storing live runtime state
* control claims derived from observation-only endpoints
* schema-present booleans being used as runtime-present booleans

#### Canonical anti-regression hooks

`lint_ports.sh`
Fails if forbidden port literals appear in protected files.

`check_preflight.sh`
Fails if startup script bypasses `preflight.py`.

`check_audit_truth.sh`
Fails if compact audit conflates evidence classes or marks placeholders as complete.

`inventory_schema_check.py`
Fails if required inventory files are missing or malformed.

---

### 14. Skill extraction policy
Do not create a skill just because something happened once. Create a skill if at least one is true:
* used twice or more
* caused one major failure
* has high blast radius
* encodes a truth discipline
* is expensive to rediscover
* is needed for handoffs
* will likely recur across repo tasks

#### At the end of every major pass, require:
`skills-to-make` for doctrine and reusable workflows
`code-to-extract` for duplicated mechanics that should become modules, linters, or assertions

#### Mandatory extraction questions
* What did I have to remember manually?
* What did I diagnose twice?
* What would a flash agent miss here?
* What caused false confidence?
* What should become code?
* What should become an audit assertion?
* What should become a documented skill?

---

### 15. Recommended default workflow
For any serious task:
1. run `/capabilities-audit`
2. run `/beta`
3. classify surfaces and blockers
4. if startup/inference is involved, run preflight
5. perform smallest repair with `/alpha`
6. execute only if `/gamma` is justified
7. inspect with `/theta`
8. finish with extraction review

---

### 16. Immediate high-value additions
If you implement only a small set now, do these first:
1. `src/gamma_runtime/preflight.py`
2. `src/gamma_runtime/config.py`
3. `analysis/compact_audit.py` with evidence classes
4. `/capabilities-audit`
5. `/beta`
6. `src/gamma_runtime/model_readiness.py`
7. `src/gamma_runtime/inventory_schema.py`
8. `src/gamma_runtime/audit_assertions.py`
9. `startup-truth-criteria` skill
10. `evidence-surface-grounding` skill

---

### 17. Flash-agent readiness target
A flash-ready stack is one where a weaker model can:
* find the right interpreter
* detect missing dependencies immediately
* discover the correct ports from config
* distinguish memory from config from runtime
* tell whether it can observe or control
* refuse to claim success too early
* find a compact audit surface instead of rediscovering the repo
* detect model-not-loaded blockers before wasting turns on higher-level debugging