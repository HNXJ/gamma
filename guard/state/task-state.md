# Current Task: Phase 1 - Training Supervision

Objective: Monitor the `FedLoRA` training process for stability and safety.

Directives:

1. Ensure `fedlora_trainer.py` is running (or start it if needed, redirecting output to `training.log`).
2. Periodically check the last 50 lines of `training.log`.
3. Search for: `NaN`, `Inf`, `Error`, or `Traceback`.
4. If divergence or failure is detected, record the exact error in `guard-state.md` and suggest stopping the run.

Status:

- Start command: `python3 scripts/fedlora_trainer.py > training.log 2>&1 &`
- Monitoring command: `tail -n 50 training.log`
