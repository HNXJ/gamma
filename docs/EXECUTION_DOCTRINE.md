# Execution Doctrine - Canonical Substrate

## 1. Control Plane Unification
* **Canonical Wrapper**: `computational/gamma/tools/cli_exec.py`
* **Canonical Audit Log**: `computational/gamma/local/run/cli_audit.jsonl`
* **Canonical Summary**: `computational/gamma/local/run/cli_audit_summary_latest.json`

## 2. Infrastructure Constraints
* **No Parallel Stacks**: Do not introduce new execution wrappers or telemetry logs.
* **Helper Utilities**: Only allowed if they do not contain independent control logic or logging.
* **Architecture Integrity**: All guardrails (timeout/watchdog, compile-gate, classification) must reside within the canonical wrapper.
* **Policy Compliance**: Any changes to instrumentation require explicit migration/deprecation paths for legacy artifacts.

## 3. Enforcement Semantics
* **Timeout Policy**: 30s ceiling for all probes; daemon processes excluded from probe-timeout logic.
* **Compile-before-run**: Mandatory for direct local .py execution targets.
* **Search Drift**: Recursive speculative searches require '--allow-grep'.

## 4. Canonical Freeze State
* **Canonical Freeze Ref**: \`v0.1.2-exec-freeze\`
* **Canonical Substrate Commit**: \`61038a315b59c73b45876d9319075a2aa8a6607a\`
* **Superceded Refs**: \`v0.1.0-exec-freeze\`, \`v0.1.1-exec-freeze\`
