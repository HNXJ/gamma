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

## SDE Game Server: Neuro-Computational Orchestrator

The Gamma repository now includes a dedicated multi-agent orchestration layer, the **SDE Game Server**, which manages scientific debate and parameter extraction tasks across independent Gemma-4 context windows.

### Game Architecture: The XYZW Protocol
The SDE Game Server models neuro-computational modeling as a game where agents (Gemma-4 context windows) participate in a multi-round debate to converge on accurate biophysical parameters. The engine evaluates the collective session using the **XYZW protocol**:

- **X (Epistemic Gain/Convergence):** A measure of informational overlap. High `x` indicates the council has converged on a shared set of scientific findings.
- **Y (Methodological Rigor):** A measure of the soundness of the proposed experimental/modeling techniques (e.g., preference for Patch-clamp vs Observation).
- **Z (Biological Plausibility):** A metric reflecting adherence to valid biological constraints.
- **W (Consensus/Stability):** A measure of team consistency and hallucination suppression. `W` approaches 1.0 when agents explicitly validate and agree with peer findings (e.g., using "I AGREE").

This system enforces an objective, rigorous, and verifiable path to scientific consensus, grounding speculative reasoning into reproducible Jaxley configurations.
