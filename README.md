# Gamma: MLX PEFT Stack & High-Fidelity Scientific Runtime

**Gamma** is a **scientific operating system** designed as a single control plane for multi-agent biophysical research. Built for **Apple Silicon (M3 Max 128GB)**, it unifies high-level Council reasoning with low-level SDE optimization into a resource-aware, sovereign research environment.

## 🏗️ The Four-Pillar Architecture
Gamma is organized around four decoupled layers to ensure scientific legitimacy and system stability:

1.  **Multi-Agent Runtime (`gamma_runtime`):** A substrate providing model residency (`SharedModelPool`), request scheduling (`InferenceScheduler`), and tool execution with forensic metric tracking.
2.  **Biophysical SDE Engine:** A decoupled optimization loop for parameter search (e.g., inhibitory conductance deficits) anchored in the **GAMMA Protocol (x, y, z, w)**.
3.  **Observability & Telemetry (The Hub):** A dedicated forensic surface separating **Maintenance Truth** (Heartbeat API) from **Science Truth** (The Ledger).
4.  **PEFT/FedLoRA Consolidation:** A mechanism for localizing scientific knowledge into persistent model adapters across distributed nodes.

## 🏛️ Paper-Anchored Skill Architecture
The Gamma Council uses the foundational scientific paper (HN et al., 2026) as its **Reference Specification**.
- **The Skill Promotion Rule:** Validated code paths (e.g., peak power detection, synchronization indices) are promoted into reusable primitives in `skills_lib.py`.
- **Audit Hardening:** All core logic and configurations are fingerprinted via **SHA-256** for courtroom-grade provenance.

## 🚀 Runtime Specifications
- **SharedModelPool:** Implements Singleton Weight Residency to minimize VRAM pressure.
- **InferenceScheduler:** Managed parallel execution with an explicit ResourceBudget and **65,536 (64k)** context windows.
- **Auto-Provisioning:** The scheduler safely auto-provisions model pools only for models registered in the declarative `configs/` registry.

## 🛠️ Repository Structure
- `src/gamma_runtime/`: Core engine, heartbeat management, and `skills_lib.py`.
- `apps/`: High-level orchestrators (e.g., `council_app.py`).
- `configs/`: Declarative identity for agents, models, teams, and families.
- `skills/`: Paper-anchored skill definitions and promotion logs.
- `dashboard/`: Telemetry UI for real-time council monitoring.

---
*Status: Phase 2 (Forensic Observability) Certified. Integrated Proof verified via live skill-call audit.*
