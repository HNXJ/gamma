# Gamma Arena: Biophysical Game for LLM-Agents

Gamma Arena is a persistent growth mission where LLM-based agents (G01-G04) collaborate to build and stabilize a biophysically valid neural network.

## 🎯 The Mission: Persistent Growth to 1000 Neurons
The goal is to autonomously grow the network from a 10-neuron bootstrap to a 1000-neuron complex system.

### Core Operating Laws
1. **Growth Gate**: A neuron-count increase is allowed ONLY if the current network passes a **1000ms run at dt 0.1** with biological validity.
2. **Runtime Freeze**: The system architecture is locked. Scientific and gameplay evolution occurs via **Patch Manifests** and **Mailbox Announcements**.
3. **Always-Active Protocol (Zero-Idle)**: The orchestrator enforces sub-second heartbeat monitoring. Any idle state is treated as a critical event requiring autonomous recovery. The system must never stop unless a rare, explicitly logged exception occurs.
4. **Autonomous Optimization**: Agents are encouraged to use **GSDR, AGSDR, and Adam** optimizers to reach stability targets.

## 🎭 The Council (G01-G04)
* **G01 (Proponent)**: Primary builder and growth planner.
* **G02 (Adversary)**: Boundary tester and critical falsifier.
* **G03 (Judge)**: Convergence auditor and acceptance gate.
* **G04 (Tester)**: Progress manager and fact-skill organizer.

## 🛠 Infrastructure
* **Hub API**: Port 8001
* **Dashboard**: Port 3012
* **Root Path**: /Users/HN/MLLM/gamma

---
*Operational Mode: Persistent Mission (S01_BOOTSTRAP)*
