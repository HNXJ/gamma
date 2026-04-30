# Gamma Arena Migration Contract (FROZEN)
Version: 1.6.0 (Phase 1.6 Hardening Complete)
Date: 2026-04-30

## 1. Authoritative Backend Routes

| Method | Route | Description | Truth Class |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/status` | Composite world snapshot | **GROUNDED** |
| `GET` | `/api/progression` | Scientific neuron ladder | **GROUNDED** |
| `GET` | `/api/agents` | Agent roster (Slots vs Agents) | **GROUNDED** |
| `GET` | `/api/persistence` | Namespaced recovery state | **GROUNDED** |
| `GET` | `/api/health` | Live heartbeat & Uptime | **GROUNDED** |
| `GET` | `/api/events/stream` | Real-time SSE telemetry | **GROUNDED** |
| `GET` | `/api/logs/raw` | Proof-of-work raw tails | **GROUNDED** |

## 2. Hardened Semantic Separations

### 2.1 Backend Slots vs Grounded Agents
- **Backend Active Slots**: Represents infrastructure model/inference capacity (e.g., "3 / 4").
- **Grounded Arena Agents**: Represents verified active agent instances found in live research logs.

### 2.2 Progression Grounding
- Progression is no longer purely inferred from patch manifests. 
- Authoritative source: `local/game001/arena_runtime_state.json` (Live world manifest).

### 2.3 Uptime Metrics
- Uptime is grounded in the monitor process start time (`APP_START_TIME`), providing a verifiable operational metric.

## 3. Discarded/Internal Routes
- `POST /api/terminal/exec`: **REMOVED** from migration scope. Command execution is handled externally; `gamma-arena` remains a read-only observability surface.

## 4. Phase 2 Readiness
- Contract is **FROZEN**.
- SSE stream is **ACTIVE**.
- Semantic split is **ENFORCED**.

**Migration to React/Vite App-Shell (Phase 2) is now AUTHORIZED.**
