# Guard: Defensive Agent Harness

Guard is a local, defensive, markdown-driven CLI agent harness. It acts as a security boundary between a Large Language Model and your local shell.

## Architecture

- **Core**: Python-based orchestration and security policy engine.
- **State**: Markdown files defining agent identity (`ego.md`), current tasks (`task-state.md`), and historical memory (`guard-state.md`).
- **Policy**: Strict deny-by-default execution boundary.

## Security Model

> [!IMPORTANT]
> Guard is NOT a process sandbox (like Docker). It is a logical policy engine that validates commands before execution.

- **No `shell=True`**: All commands are executed as list arguments via `subprocess.run`.
- **Fenced Blocks Only**: Commands are extracted exclusively from ` ```bash ` blocks.
- **Binary Allowlist**: Only a curated set of binaries (`ls`, `cat`, `git`, `python3`, etc.) are permitted.
- **Path Isolation**: Arguments containing paths are validated to ensure they remain within `GUARD_SANDBOX_DIR` or `GUARD_REPO_ROOT`.
- **Git/Python Restrictions**: Dangerous flags and subcommands are strictly blocked.

## Setup

1. **Local Model**: Ensure an OpenAI-compatible server (like LM Studio) is running.
2. **Config**: Copy `.env.example` to `.env` and update the values.
   ```bash
   cp .env.example .env
   ```
3. **Sandbox**: Create the sandbox directory.
   ```bash
   mkdir sandbox
   ```

## Usage

### Run Once
```bash
bash scripts/run_guard_once.sh
```

### Run Bounded Loop
```bash
bash scripts/run_guard_loop.sh
```

## Testing
Run the test suite with pytest:
```bash
pytest
```
