# Gemini Local Context for Gamma Labyrinth

## Scope

This file contains local coordination context for Gemini agents working in the `gamma` repo. It is not a Truth-plane receipt and does not define biological state.

## Local Clone Layout

- Gemini/Antigravity clone root: `/Users/hamednejat/gemini-gamma-labyrinth/repos/`
- Claude/Cowork clone root: `/Users/hamednejat/claude-gamma-labyrinth/repos/`

Gemini agents must work under the Gemini/Antigravity clone root unless explicitly authorized. Do not write into the Claude/Cowork clone root.

## Coordination Doctrine

GitHub Project `gamma` is the Control-plane source of truth for task coordination, issue routing, agent work status, and repo work ledger. It is not scientific Truth-plane state unless backed by Truth-plane receipts.

Assume Gemini, Antigravity, Claude, and Cowork may work in parallel. Before repo work: check issue/task ownership, run `git status`, inspect branch, fetch/pull when safe, and avoid overwriting others' work.

Use bounded commits and pull/push synchronization. For conflict isolation, use task branches or dev branches such as `dev-gemini` and `dev-claude`, then reconcile to `main` through review.

## Branch Policy

`main` is the preferred source-of-truth branch unless a repo-specific verified exception exists. `gamma-protocol` may use `master`. If branch doctrine conflicts with observed repo state, route to DELTA before execution.

## No-Guessing Rule

If an expected file, repo, config, memory file, branch, issue, or source document is missing or ambiguous, do not invent it. Ask before creating, loading, cloning, renaming, moving, replacing, or editing it.

## Truth Discipline

No active neuron count, accepted circuit state, growth target, or scientific truth may be asserted from memory. If no current Truth-plane receipt is available, use `truth_mode: truth_safe_unverified`.
