# Gamma Arena: Biophysical Game for LLM-Agents

Gamma Arena is a persistent growth mission where runtime-configured players and judges collaborate to build and stabilize a biophysically valid neural network.

## 🎯 The Mission: Continuous Growth (N → N+1)
Gamma is a protocolized scientific discovery engine where the objective is to autonomously grow the neural substrate by exactly one biologically justified neuron at a time.

### Core Operating Doctrine
1. **N → N+1**: Every expansion must be a single, justified step from current truth.
2. **Growth Gate**: A neuron-count increase is allowed ONLY if the candidate network passes canonical Judge validation with a receipt.
3. **Trial vs. Truth**: Trial simulations are scratch artifacts. Only Judge-validated PASS receipts can commit new truth.
4. **Law of the Protocol**: Mission contracts are defined in `gamma-protocol`.

## 🎭 Participants (1 Judge + 4 Players)
* **Judge**: The final arbiter of mission success and truth promotion.
* **runtime-configured players**: Flexible identities (Builder, Tuner, Analyst, Tester) performing the expansion quest.

## 🛠 Infrastructure
* **Hub API**: Port 8001
* **Dashboard**: Port 3012
* **Root Path**: configured runtime workspace; see local non-secret context config


## Branch Doctrine

`main` is the stable branch for reviewed, reusable backend/control-plane state. `office-dev` is a development and integration branch and must not be merged wholesale into `main` without explicit THETA approval of the full commit scope.

Stable promotions should be exact, reviewed, and minimal. Runtime, solver, adapter, persistence, Supabase, receipt, or truth-state changes require explicit review before stable promotion.


---
*Operational Mode: Persistent Mission (S01_BOOTSTRAP)*

## Coordination

This repository follows the [GAMMA-BUS Coordination Doctrine](GEMINI.md). Agents should refer to `GEMINI.md` for specific instructions and coordination rules.
