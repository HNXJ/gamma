# Gamma Core Configuration Layer

This directory contains the canonical configuration definitions for the Gamma Arena / Gamma runtime.

## Files

- `runtime_core.json`: The primary, version-controlled source of truth for configuration defaults.
- `README.md`: This documentation.

## Config Taxonomy

### `environment`
Metadata about the execution environment.
- `label`: Human-readable identifier for the machine/setup.
- `is_cloud`: Boolean flag for cloud vs local semantics.

### `paths`
Root-relative or absolute paths for storage and discovery.
- `world_root`: The absolute path to the project root (defaulting to the developer's workspace).
- `data_root`: Base directory for persistent data (e.g., `local`).
- `run_root`: Directory for transient runtime state (e.g., `local/run`).
- `mail_root`: Dedicated directory for player mailbox JSON files.
- `inventory_root`: Dedicated directory for player inventory/item JSON files.
- `logs`: Log storage.
- `snapshots`: World state snapshots.

### `network`
Port assignments and binding hosts.
- `hub_port`: internal bridge (8001).
- `monitor_port`: Canonical External API (3013).
- `ui_port`: Dashboard UI (3012).
- `lms_port`: LMS Inference Server (1234).

### `timing`
Operational intervals and timeouts.
- `heartbeat_interval_seconds`: Frequency of the system health pulse (Default: 10.0s).

## Overrides

Machine-specific or session-specific overrides should be placed in `local/runtime_overrides.json`. This file is excluded from git and will be deep-merged over `runtime_core.json`.

Environment variables prefixed with `GAMMA_` can also override any key using double-underscore `__` as a separator (e.g., `GAMMA_TIMING__HEARTBEAT_INTERVAL_SECONDS=5.0`).
