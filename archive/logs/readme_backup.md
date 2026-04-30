# Gamma: MLX PEFT Stack & High-Fidelity Scientific Runtime

**Gamma** is a dedicated research environment for multi-agent biophysical modeling and Slow-Learning consolidation. Built for **Apple Silicon (M3 Max 128GB)**, it transitions the repository from a collection of scripts to a sovereign agentic OS where reasoning (Council) and biophysical optimization (SDE Engine) are unified under a single, resource-aware runtime.

## 🚀 Realized Functionality

### 1. The Gamma Runtime
- **SharedModelPool:** Implements **Singleton Weight Residency**. Models load once into unified memory; multiple logical agents (Macro, Meso, Micro) multiplex across shared weights to minimize memory duplication.
- **InferenceScheduler:** Managed parallel execution with an explicit **ResourceBudget**. Automatically tracks and reserves KV-cache token pools, enforcing 8-bit quantization (`float8_e4m3fn`) and 16k context windows to protect hardware from Jetsam kills.
- **Blackboard Pattern:** Centralized state object for multi-agent deliberation. Replaces direct agent-to-agent coroutines with an auditable, write-once/read-many state that acts as the "Common Operating Picture" for scientific convergence.
- **Hub API:** A zero-dependency REST interface providing a handshake between the M3 Max backend and the **Gamma Hub Dashboard**.

### 2. SDE Engine & Biophysical Optimization
- **The SDE Solver:** A refactored biophysical optimization engine decoupled from shadow agent logic. It uses the `InferenceScheduler` for all LLM-assisted parameter searches.
- **The GAMMA Protocol (x, y, z, w):**
    - **x (Epistemic Gain):** Differentiable Loss (MSE) tracking scientific accuracy.
    - **y (Methodological Rigor):** Measured JIT compilation and federated efficiency.
    - **z (Neurobiological Ground Truth):** Soft-penalized biological adherence via exponential decay.
    - **w (Algorithmic Coherence):** Distributed system stability and consensus metrics.
- **$\mathcal{L}_{council}$:** A global loss function where agents minimize the variance between biological plausibility ($z$) and code stability ($w$).

### 3. Advanced PEFT Stack
- **Composite Adapters (FedLoRA):** Layered adaptation via `forward_delta` additive composition. Supports simultaneous "Global Council" and "Personal" LoRA/DoRA adapters without weight double-counting.
- **Episodic Consolidation:** Adapters are trained only on high-consensus, validated traces staged on the Blackboard, preventing hallucination bleed into the model weights.

## 🛠️ Repository Structure

- `src/gamma_runtime/`: Core engine, scheduler, and model pool management.
- `src/sde_engine/`: Biophysical optimization metrics and solvers.
- `apps/`: High-level orchestrators (e.g., `CouncilApp`, `SchizPilot`).
- `dashboard/`: Scientific telemetry and Guard sentinel UI.
- `configs/`: Declarative `AgentSpec` and `ModelSpec` configurations.

## Status

- [x] **Core Runtime:** SharedModelPool & InferenceScheduler established.
- [x] **Communication:** Blackboard pattern implemented for unified state.
- [x] **Orchestration:** UnifiedOrchestrator & Hub API bridge live.
- [x] **Verification:** Schizophrenia Multi-Scale Pilot (g_inh) successfully executed.
- [ ] **Consolidation:** Automated Episodic FedLoRA training loop.
- [ ] **Stability:** Evaluation framework for catastrophic forgetting.

## The First Flight
The stack has successfully completed its **Schizophrenia Multi-Scale Pilot**, matching the Berlin MEG 1/f spectral slope flattening by optimizing inhibitory conductance ($g_{inh}$) deficits across a quad-agent ensemble. This marks the transition from theoretical architecture to a production-ready scientific research engine.
