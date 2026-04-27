# Current Task: Phase 1 - Training Supervision

Objective: Monitor the `FedLoRA` training process for stability and safety.

Directives:

1. Ensure `fedlora_trainer.py` is running (or start it if needed, redirecting output to `training.log`).
2. Periodically check the last 50 lines of `training.log`.
3. Search for: `NaN`, `Inf`, `Error`, or `Traceback`.
4. If divergence or failure is detected, record the exact error in `guard-state.md` and suggest stopping the run.

## 🚨 CRITICAL HALT PROTOCOL

If the string `NaN` or a sudden, catastrophic spike in the loss value is detected in `training.log`:

1. You are explicitly authorized to terminate the training run to preserve VRAM.
2. Execute `pgrep -f fedlora_trainer.py` to isolate the Process ID (PID).
3. Execute `kill -9 <PID>` to forcefully halt the process.
4. Document the exact termination timestamp and the fatal loss value in `guard-state.md`.

Status:

- Start command: `python3 scripts/fedlora_trainer.py > training.log 2>&1 &`
- Monitoring command: `tail -n 50 training.log`
