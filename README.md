# Gamma: MLX PEFT Stack & High-Fidelity Scientific Runtime

**Gamma** is a dedicated research environment for multi-agent biophysical modeling and Slow-Learning consolidation. Built for **Apple Silicon (M3 Max 128GB)**, it transitions the repository from a collection of scripts to a sovereign agentic OS where reasoning (Council) and biophysical optimization (SDE Engine) are unified under a single, resource-aware runtime.

## 🏛️ Paper-Anchored Skill Architecture
The Gamma Council uses the foundational scientific paper (HN et al., 2026) as its **Reference Specification**. The paper defines the **visual grammar** of figures, the **metric ontology**, and the **objective scaffolding** for all research tasks.

### 📋 The Skill Promotion Rule
To move from ephemeral scripts to a stable neuroscience toolkit, the council enforces the **Promotion Rule**:
- Any validated code path that produces a paper-aligned artifact (e.g., Fig. 3 Raster, Fig. 8 Spectrogram) is auto-promoted into a reusable skill.
- **Promotion Test:** Successful Execution, Structural Validity, Reusability, Strict Typing, and Paper Alignment.
- **Audit Hardening:** All core logic (skills, configs) is fingerprinted via **SHA-256** to ensure courtroom-grade provenance.
- Agents are mandated to check `skills/SKILLS.md` before writing new analysis code.

## 🚀 Realized Functionality (Production-Grade Audit)

### 1. The Gamma Runtime
- **SharedModelPool:** Implements **Singleton Weight Residency**. Models load once into unified memory; agents multiplex across shared weights.
- **InferenceScheduler:** Managed parallel execution with an explicit **ResourceBudget** (8-bit quantization, 64k/65536 context).
- **Blackboard Pattern:** Centralized state object for multi-agent deliberation.

### 2. SDE Engine & Biophysical Optimization
- **The SDE Solver:** A biophysical optimization engine decoupled from agent logic.
- **The GAMMA Protocol (x, y, z, w):**
    - **x (Epistemic Gain):** Differentiable Loss (MSE) tracking scientific accuracy.
    - **y (Methodological Rigor):** Measured JIT compilation and federated efficiency.
    - **z (Neurobiological Ground Truth):** Soft-penalized biological adherence via exponential decay.
    - **w (Algorithmic Coherence):** Distributed system stability and consensus metrics.

### 3. Forensic Observability (Phase 2)
Gamma implements a strict **Separation of Concerns** between maintenance and science:
- **Maintenance Truth (Heartbeat API):** Real-time monitoring of agent health, token consumption, and input/output sizes. Served via a dedicated `/api/heartbeat` endpoint.
- **Science Truth (The Ledger):** Auditable record of scientific results and parameter accepted by the bridge.

## 🛠️ Repository Structure
- `src/gamma_runtime/`: Core engine and `skills_lib.py`.
- `skills/`: Paper-anchored skill definitions and promotion templates.
- `apps/`: High-level orchestrators (e.g., `SchizPilot`).

---
*Reference Paper: HN et al. (2026) - Generalized Slow-Learning Discovery and Reporting (GSDR).*
