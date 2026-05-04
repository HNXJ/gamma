# Gamma Branch Doctrine

## Stable branch

`main` is the stable branch for reviewed, reusable Gamma backend/control-plane state.

Stable `main` must not receive broad development merges by default. It should receive exact, reviewed, minimal patches with explicit validation evidence.

## Development branch

`office-dev` is a development and integration branch. It may contain broad runtime, orchestration, tutorial, adapter, persistence, or experimental work that is not safe to promote wholesale.

Do not merge `office-dev` into `main` unless a THETA audit explicitly approves the full commit scope.

## Promotion rule

Promotions from development branches to stable `main` must be one of:

1. exact-file patch promotion;
2. cherry-pick of a reviewed commit with safe scope;
3. a full merge only after full-scope THETA approval.

If a candidate promotion touches solver, adapter, persistence, Supabase, receipt, truth-state, substrate, or ledger files, stop and require explicit THETA review.

## Truth-plane discipline

Scientific truth is only persistent state committed from approved, converged, adapter-mediated, receipt-backed execution gates.

UI surfaces, dashboards, project-board issues, logs, runtime chat, and game chatter are observation/control artifacts. They do not create or prove scientific truth.

## Protocol dependency boundary

`gamma-protocol` is the Markdown-only doctrine/specification repository. It is not a runtime package dependency for `gamma`.

Runtime validation logic that `gamma` needs must live inside `gamma` or be generated through an explicit, reviewed bridge.
