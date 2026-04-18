# Gamma: MLX LLM Low-Rank Fine-Tuning & Multi-Agent Episodic Learning

**Gamma** is a dedicated repository for the implementation, experimentation, and production hardening of parameter-efficient fine-tuning (PEFT) methods—specifically Low-Rank Adaptation (LoRA) and Weight-Decomposed Low-Rank Adaptation (DoRA)—using the **MLX framework on Apple Silicon**.

It serves as the long-term consolidation mechanism for a distributed, multi-LLM cluster (e.g., an 8-node homogeneous Gemma-4 MLX cluster), behaving like a distributed scientific institute where learning is treated as a **slow consolidation mechanism** derived from validated traces, separate from the live reasoning loop.

## Core Capabilities

- **Model-Agnostic PEFT Stack:** Designed to target generic linear projections across families (Gemma, Llama, Mistral, Qwen) using MLX array operations.
- **Composite Adapters (FedLoRA):** Supports an episodic, federated, and rollback-able adaptation pipeline. Multiple adapters (e.g., a "Global Council" LoRA and a "Node-Personal" LoRA) are layered via a `CompositeAdapter` using a bit-exact `forward_delta` additive composition logic that prevents base weight double-counting.
- **Episodic Learning (Consolidation Mode):** Adapters are trained only during explicit consolidation windows using high-consensus, validated traces (no raw or hallucinated data enters the weights).
- **Gamma DNA Protocols:** A structured, epigenetic tracking system (using `.gamma` files) that anchors agentic actions into A (Ingredients), B (Preparation), C (Cooking), and D (Serving) phases for absolute reproducibility and hardening.
- **MCP Server Hardening:** Hardened integration for local environments (such as LM Studio MCP resolution) ensuring unified variable injection and node-aware paths.

## Status

- [x] Repository Initialized
- [x] Universal `forward_delta` logic for multi-adapter stacking verified
- [x] Loss functions and parameter filtering established (`train_lora_mlx.py`)
- [x] MCP LM Studio integration hardened
- [ ] Hyperparameter Optimization
- [ ] Evaluation Framework & Catastrophic Forgetting Mitigation

## Architecture & Philosophy

Gamma enforces a hard separation between **runtime cognition** (reading, routing, debate) and **slow learning** (federated aggregation, adapter training). The base model remains frozen and stable. Validated experiences are converted into low-rank adapter deltas, allowing role specialization without forking the base model and guaranteeing safe, reversible updates.

For a full breakdown of the clustered federated LoRA vision, review `GAMMA_FEDLORA_PLAN.md`.
