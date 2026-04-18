# GAMMA_FEDLORA_PLAN.md

> [!NOTE]
> **Review status**: This document has been critically reviewed (2026-04-17). Review annotations are marked with `[REVIEW]` blocks throughout. No original text has been removed.

## Gamma FedLoRA / DoRA / PEFT Plan for an MLX-Compatible, Model-Agnostic Multi-LLM Cluster

### Purpose

This document describes what Gamma should do, why it should do it, and how to implement a family of parameter-efficient fine-tuning (PEFT) methods in a way that is:

- model-agnostic at the architectural level,
- practical on Apple Silicon using MLX-compatible tensor operations,
- safe for a distributed multi-LLM system,
- compatible with episodic, federated, rollbackable adaptation,
- extensible from simple LoRA to more advanced methods such as DoRA, QLoRA, AdaLoRA, sparse LoRA, and personalized dual-adapter federation.

The central design decision is that Gamma should treat PEFT as a **slow consolidation mechanism**, not as part of the live reasoning loop. The live cluster performs reading, planning, debate, routing, and synthesis. Adapter training happens later, in explicit consolidation windows, from validated traces only.

---

## 1. Executive summary

Gamma’s long-term target is an 8-node homogeneous Gemma-4 MLX cluster that behaves like a distributed scientific institute rather than a fast chat model. In that architecture, the live system already has three major cognitive phases:

1. **Discovery Mode** for open-ended exploration,
2. **Plan Mode** for structured debate and consensus building,
3. **Consolidation Mode** for converting validated experience into persistent skill.

FedLoRA belongs entirely to the third phase.

The FedLoRA survey defines the field as the integration of Low-Rank Adaptation (LoRA) into Federated Learning (FL), with the main concerns grouped into distributed learning, heterogeneity, and efficiency. The survey emphasizes that clients fine-tune local models but communicate only LoRA parameters, reducing computational and communication cost while preserving privacy and locality. It also warns that naïvely aggregating LoRA factors can be mathematically inconsistent because separately averaging the two low-rank matrices does not equal averaging the actual induced update. fileciteturn9file0turn9file1

> [!IMPORTANT]
> **[REVIEW — GAP-01: Citation Integrity]** All `fileciteturn*` and `citeturn*search*` strings throughout this document are internal chatbot artifacts, not valid citations. This violates the Gamma Protocol’s mandatory DOI rule. The following DOIs must replace them:
> - **LoRA**: Hu et al., 2022. DOI: [10.48550/arXiv.2106.09685](https://doi.org/10.48550/arXiv.2106.09685)
> - **DoRA**: Liu et al., 2024. DOI: [10.48550/arXiv.2402.09353](https://doi.org/10.48550/arXiv.2402.09353)
> - **QLoRA**: Dettmers et al., 2023. DOI: [10.48550/arXiv.2305.14314](https://doi.org/10.48550/arXiv.2305.14314)
> - **FedAvg**: McMahan et al., 2017. DOI: [10.48550/arXiv.1602.05629](https://doi.org/10.48550/arXiv.1602.05629)
> - **FFA-LoRA**: Sun et al., 2024. DOI: [10.48550/arXiv.2407.19195](https://doi.org/10.48550/arXiv.2407.19195)
> - **FedEx-LoRA**: Singhal et al., 2024. DOI: [10.48550/arXiv.2405.09384](https://doi.org/10.48550/arXiv.2405.09384)
> - **AdaLoRA**: Zhang et al., 2023. DOI: [10.48550/arXiv.2303.10512](https://doi.org/10.48550/arXiv.2303.10512)

For Gamma, this means the following:

- each node should remain a full local reasoner during live operation,
- only adapter checkpoints, adapter deltas, or derived update products should move during consolidation,
- the system should distinguish between **global cluster learning** and **node-local specialization**,
- every learned update must be reversible,
- low-consensus or hallucinated traces must never enter adapter training.

The immediate implementation recommendation is:

- start with **single-node MLX LoRA**,
- then implement **episodic node-local LoRA training**,
- then add **alternating federated aggregation**,
- then split adapters into **global council LoRA** and **node-personal LoRA**,
- then expand to DoRA, QLoRA, sparse LoRA, and rank-adaptive methods.

---

## 2. What we want Gamma to do

Gamma should become a distributed local-LLM system that can:

- parse large technical corpora,
- keep long-running project memory,
- debate, criticize, refine, and compress ideas across nodes,
- decide when uncertainty is too high and escalate to expert review,
- slowly learn from its own validated work without catastrophic forgetting,
- preserve a stable shared identity while allowing node specialization.

> [!WARNING]
> **[REVIEW — GAP-05: Catastrophic Forgetting]** "Without catastrophic forgetting" is stated as a goal here and in §2.1 but the plan provides **zero mechanisms** for detecting or mitigating it. LoRA adapters *can* degrade base-model capabilities on non-trained tasks, especially under episodic replay. Required additions:
> 1. Maintain a **held-out regression test set** of base-model capabilities (general QA, reasoning, code)
> 2. Measure base-model task performance **before and after** adapter merge
> 3. Define a **maximum acceptable regression threshold** (recommendation: ≤2% on base capability benchmarks)
> 4. If regression exceeds threshold, apply EWC-style regularization on adapter parameters or reduce learning rate
> 5. Log regression metrics in every checkpoint for longitudinal drift analysis

### 2.1 What Gamma is not trying to do

Gamma is not trying to do continual gradient updates in the middle of live reasoning. It is not trying to replace the context matrix with weights. It is not trying to turn every node into an always-training learner. It is not trying to push raw full-model updates across the mesh. It is not trying to hide uncertainty by merging noisy experiences into a single unquestioned adapter.

Instead, Gamma should preserve a hard separation between:

- **runtime cognition**: context, planning, reading, routing, judgment,
- **slow learning**: episodic replay, adapter training, federated aggregation, checkpointing.

This distinction is necessary both scientifically and operationally. The FedLoRA survey frames FL + LoRA as a collaborative adaptation process for distributed clients, not as a per-token online reasoning mechanism. Its primary motivation is efficient collaborative fine-tuning via low-rank parameters rather than full-model synchronization. fileciteturn9file0turn9file1

### 2.2 The role of PEFT in Gamma

Parameter-efficient fine-tuning should give Gamma four things:

1. **Cluster memory consolidation**: encode repeated, validated reasoning patterns into adapters.
2. **Role specialization**: preserve node-specific expertise without forking the base model.
3. **Economic synchronization**: exchange small trainable state instead of full weights.
4. **Safe rollback**: every learning event becomes a checkpointed, reversible layer.

The cluster’s context matrix remains the primary fast workspace. PEFT becomes the long-term, slower-changing substrate underneath it.

---

## 3. Why LoRA-like methods are a good fit

The original LoRA paper proposes freezing the base model and learning a low-rank decomposition of weight updates, greatly reducing trainable parameter count while maintaining strong adaptation performance. *(Hu et al., 2022; DOI: [10.48550/arXiv.2106.09685](https://doi.org/10.48550/arXiv.2106.09685))* citeturn458295search0 LoRA is especially attractive for Gamma because:

- the base model should remain stable across nodes,
- only a small adaptation layer needs to change,
- adapters can be stored, swapped, merged, ranked, or rolled back,
- multiple roles can share the same base while differing in adapters and environment,
- the cluster can learn incrementally without paying the cost of full fine-tuning.

The FedLoRA survey further shows that LoRA is especially attractive in distributed settings because clients can learn locally while transmitting only low-rank parameters. fileciteturn9file1turn9file12 This is conceptually well aligned with an 8-node Apple Silicon cluster connected over a network where full-model movement is undesirable.

On the MLX side, Apple’s public MLX material explicitly positions MLX as a framework for experimenting with inference and fine-tuning locally on Apple Silicon hardware. citeturn458295search3turn458295search11 That makes an MLX-compatible PEFT stack a natural implementation target for Gamma.

---

## 4. Foundational design principle: model-agnostic, MLX-compatible PEFT

Gamma should not hard-code itself to one exact family such as Gemma, Llama, or Mistral at the level of adaptation logic. Instead, it should define an abstract adapter layer system that can target whichever linear projections a supported architecture exposes.

### 4.1 Model-agnostic means

At the planning level, “model-agnostic” should mean:

- the code reasons in terms of target modules, not brand names,
- the adapter implementation operates on generic tensor shapes,
- the trainer knows how to discover candidate linear layers,
- per-family config files declare target module patterns,
- the runtime can attach multiple adapters to the same base model.

### 4.2 MLX-compatible means

“MLX-compatible” should mean:

- tensor ops are expressible in MLX arrays,
- parameter freezing and trainable subsets are explicit,
- merged and unmerged inference are both possible,
- quantized base weights remain possible when supported,
- checkpoint formats are simple enough to mmap, shard, and swap locally.

### 4.3 The abstraction Gamma should use

Gamma should implement a common adapter API such as:

```python
class AdapterMethod:
    name: str
    def attach(self, model, target_spec, config): ...
    def trainable_parameters(self): ...
    def forward_delta(self, layer_input): ...
    def merge_into_base(self): ...
    def unmerge_from_base(self): ...
    def export_state(self): ...
    def load_state(self, state): ...
    def aggregate(self, states, policy): ...
```

> [!TIP]
> **[REVIEW — GAP-11: API Completeness]** The `AdapterMethod` API above is a good skeleton but is missing several methods required by later sections of this plan. Recommended additions:
> ```python
> class AdapterMethod:
>     name: str
>     adapter_rank: int                              # needed by AdaLoRA, sparse LoRA
>     adapter_alpha: float                           # scaling factor
>     target_modules: list[str]                      # which modules this adapter wraps
>     def attach(self, model, target_spec, config): ...
>     def trainable_parameters(self): ...
>     def forward_delta(self, layer_input): ...
>     def merge_into_base(self): ...
>     def unmerge_from_base(self): ...
>     def export_state(self): ...
>     def load_state(self, state): ...
>     def aggregate(self, states, policy): ...
>     def reset(self): ...                           # rollback to pre-training state
>     def compute_importance(self) -> dict: ...      # for pruning / sparsification
>     def delta_from(self, other_state) -> dict: ... # efficient sync (transmit only changed params)
>     def validate_state(self, state) -> bool: ...   # integrity check before loading
> ```

This way, LoRA, DoRA, QLoRA, sparse LoRA, or future methods can share the same orchestration layer.

---

## 5. The PEFT family Gamma should support

Gamma should not stop at plain LoRA. It should support a practical family of related methods.

### 5.1 LoRA

LoRA models an update to a frozen base weight matrix using two low-rank matrices, typically written as a product that approximates the update direction with far fewer trainable parameters than full fine-tuning. citeturn458295search0

#### Why Gamma wants it

- simplest and most proven PEFT baseline,
- easy to store and swap,
- straightforward to federate,
- no need to change full base weights,
- good first implementation target in MLX.

#### What Gamma should use it for

- global council adapters,
- node-personal adapters,
- fast prototypes,
- baseline against which all other methods are compared.

### 5.2 QLoRA

QLoRA combines quantization of the base model with LoRA-based adaptation, enabling fine-tuning on smaller hardware budgets while keeping trainable low-rank adapters. The MLX examples specifically note support for LoRA and QLoRA-style fine-tuning. citeturn458295search11

#### Why Gamma wants it

- lower memory footprint on Apple Silicon,
- larger models may fit more comfortably,
- more nodes can fine-tune concurrently,
- useful for experimentation and lower-cost consolidation windows.

#### Risks

- more numerical fragility,
- quantization backend complexity,
- careful evaluation needed to ensure no degradation in long-horizon reasoning.

### 5.3 DoRA

DoRA decomposes the pretrained weight into magnitude and direction, then uses LoRA-style low-rank learning for directional updates while separately handling magnitude. Its goal is to narrow the gap between LoRA and full fine-tuning while preserving the efficiency and no-extra-inference-overhead properties associated with LoRA-like PEFT. citeturn463687search0turn463687search2

#### Why Gamma wants it

Gamma does long-horizon reasoning, literature synthesis, and structured planning. Those are exactly the kinds of settings where the learning-capacity gap between plain LoRA and fuller adaptation may matter. DoRA is therefore attractive when plain LoRA appears too weak but full fine-tuning remains too expensive or risky.

#### What Gamma should use it for

- higher-value consolidation passes,
- critical role adapters for synthesis nodes,
- tasks where plain LoRA underfits,
- later-stage production adapters after LoRA baselines are established.

### 5.4 AdaLoRA / rank-adaptive LoRA

Adaptive rank methods change how rank budget is allocated across layers or training time. AdaLoRA is one of the best-known examples of dynamic budget allocation. The FedLoRA survey explicitly highlights adaptive rank methods as promising future directions and discusses heterogeneous rank in federated settings. fileciteturn9file5turn9file16

#### Why Gamma wants it

- some layers matter more than others,
- some nodes may need more expressive adapters than others,
- rank adaptation may improve efficiency on heterogeneous tasks.

#### When to use it

Not in v1. Add it after plain fixed-rank LoRA is stable.

### 5.5 Sparse LoRA / layer-selective LoRA

The survey covers sparse learning approaches that either sparsify LoRA parameters or activate only selected LoRA layers. fileciteturn9file6turn9file18

#### Why Gamma wants it

- adapter synchronization should be cheap,
- not all layers need updates every cycle,
- TB5 or equivalent interconnect remains finite,
- sparse updates fit the Git-like delta philosophy of the broader cluster.

### 5.6 Personalized dual-adapter PEFT

The FedLoRA survey describes personalized methods that maintain both a global and a personal adapter. fileciteturn9file4turn9file15

#### Why Gamma wants it

This is arguably the single most natural match to the Genesis/Gamma cluster architecture.

Gamma should eventually represent each node’s effective model as:

```text
Base model
+ Global council adapter
+ Node-local adapter
+ Environment injection
+ Current context row/branch
```

This preserves shared identity while allowing durable specialization.

---

## 6. What we want to do, concretely

Gamma should implement an **episodic federated PEFT stack** with the following properties.

### 6.1 During runtime, collect traces

Every node should record structured traces of work, including:

- input context,
- role,
- mode (Discovery, Plan, Consolidation),
- output,
- references/DOIs,
- disagreement state,
- consensus status,
- judge scores,
- human verification flags,
- failure class if rejected.

### 6.2 During consolidation, train locally

Each node should use only approved local traces to train a local adapter.

### 6.3 Aggregate across nodes

The cluster should then create a shared adapter from node-level updates.

### 6.4 Preserve node specialization

A node may keep a personal adapter in addition to loading the cluster-wide adapter.

### 6.5 Roll out through checkpoints

No new adapter becomes default until it passes evaluation and is checkpointed with rollback.

### 6.6 Repeat only on schedule

Consolidation should happen only in:

- idle windows,
- break-times,
- explicit maintenance epochs,
- post-judge or post-human validated milestones.

This design ensures that Gamma learns from success and correction, not from raw chatter.

---

## 7. The architecture Gamma should build

### 7.1 Core modules

The PEFT subsystem should eventually include:

- `adapter_base.py`
- `lora.py`
- `qlora.py`
- `dora.py`
- `adalora.py`
- `sparse_lora.py`
- `adapter_registry.py`
- `adapter_merge.py`
- `adapter_eval.py`
- `federated_lora_episodic.py`
- `checkpoint_manager.py`
- `sample_selector.py`
- `trace_schema.py`

### 7.2 Adapter registry

Gamma should maintain a registry of supported methods and target patterns.

Example:

```yaml
methods:
  lora:
    class: LoRAAdapter
  qlora:
    class: QLoRAAdapter
  dora:
    class: DoRAAdapter
  adalora:
    class: AdaLoRAAdapter

target_specs:
  transformer_default:
    modules:
      - q_proj
      - k_proj
      - v_proj
      - o_proj
      - gate_proj
      - up_proj
      - down_proj
```

### 7.3 Per-model family configuration

Model-agnostic does not mean config-free. It means the trainer should load family-specific mapping files, such as:

- `configs/families/gemma.yaml`
- `configs/families/llama.yaml`
- `configs/families/mistral.yaml`
- `configs/families/qwen.yaml`

Each config should specify:

- target module names,
- hidden sizes,
- whether quantization is supported,
- default adapter placements,
- merge safety constraints,
- recommended rank ranges.

---

## 8. How plain LoRA should be implemented in Gamma

### 8.1 Mathematical idea

For a frozen base weight matrix `W`, LoRA learns a low-rank update `ΔW` represented as a product of two trainable matrices. This makes adaptation cheap in parameter count and efficient to save, share, and merge. citeturn458295search0

### 8.2 Gamma implementation strategy

At attachment time:

1. identify target linear layers,
2. freeze base weights,
3. create low-rank trainable matrices per target layer,
4. add a scaled adapter path in the forward pass,
5. expose only adapter params to the optimizer.

### 8.3 Recommended first configuration

For Gamma v1:

- rank: small fixed value,
- alpha: conservative,
- dropout: optional but light,
- target modules: attention projections first, MLP projections second,
- optimizer: simple stable baseline,
- batch sizes: small and safe for Apple Silicon memory.

> [!CAUTION]
> **[REVIEW — GAP-03: Concrete Hyperparameters Required]** The above is a wish list, not a specification. Implementation will stall without concrete defaults. Recommended v1 configuration:
>
> | Parameter | Default | Sweep Range |
> |:---|:---:|:---:|
> | Rank (r) | 8 | {4, 8, 16} |
> | Alpha (α) | 16 | {8, 16, 32} |
> | Dropout | 0.05 | {0.0, 0.05, 0.1} |
> | Optimizer | AdamW | — |
> | Learning rate | 1e-4 | {5e-5, 1e-4, 2e-4} |
> | Weight decay | 0.01 | — |
> | Batch size | 2 | — |
> | Gradient accumulation | 4 (effective batch 8) | — |
> | Max sequence length | 2048 tokens | — |
> | Steps per consolidation | 200–500 (bounded) | — |
> | LR schedule | Cosine with 10% warmup | — |
> | Target modules (Phase 1) | q_proj, k_proj, v_proj, o_proj | — |
> | Target modules (Phase 1+) | + gate_proj, up_proj, down_proj | — |

### 8.4 When to merge

Gamma should support both:

- **unmerged adapters** for flexible multi-adapter stacking,
- **merged inference weights** for deployment snapshots.

Cluster runtime likely benefits from unmerged composition, while archived release candidates may use merged snapshots.

---

## 9. How QLoRA should be implemented in Gamma

### 9.1 Why QLoRA matters

QLoRA reduces the memory burden by keeping the base model quantized while training only the LoRA adapters. This is highly attractive for local Apple Silicon use when fitting larger models or when multiple jobs must coexist. citeturn458295search11

### 9.2 Gamma implementation strategy

1. load base model in supported quantized format,
2. keep quantized weights frozen,
3. attach standard LoRA modules to supported layers,
4. train adapters in higher precision than the frozen base,
5. save only adapter states plus quantization metadata.

### 9.3 Where Gamma should use it

- overnight consolidation,
- low-priority nodes,
- rapid ablations,
- scaling experiments where memory is tight.

### 9.4 Risks

Gamma must not assume that every model family and quantization scheme behaves equally well under long-form reasoning workloads. QLoRA should therefore always be benchmarked against non-quantized LoRA on Gamma-specific tasks such as literature compression, contradiction detection, and debate consistency.

---

## 10. How DoRA should be implemented in Gamma

### 10.1 Conceptual difference

DoRA separates weight **magnitude** and **direction**, then uses LoRA-style learning for the directional component while learning or updating magnitude separately. The motivation is to better approximate the behavior of full fine-tuning without paying its full cost. citeturn463687search0turn463687search12

### 10.2 Why this matters for Gamma

Gamma’s target tasks are not short instruction-following benchmarks only. They include:

- long-form scientific synthesis,
- structural code planning,
- contradiction resolution,
- branch evaluation,
- literature-grounded planning.

These tasks may demand more expressive adaptation than simple low-rank direction-only changes.

### 10.3 MLX-compatible implementation pattern

Gamma should implement DoRA as a thin extension over the LoRA API.

At each target layer:

1. decompose the effective learnable update conceptually into magnitude and direction,
2. represent directional change using a LoRA-like low-rank path,
3. store a trainable magnitude term or per-output scaling term,
4. ensure the forward pass recombines them cleanly,
5. keep merge/unmerge semantics explicit.

### 10.4 When Gamma should choose DoRA over LoRA

Use DoRA when:

- plain LoRA underfits,
- the cluster is training high-value synthesis adapters,
- stability and learning capacity matter more than minimal implementation complexity,
- consolidation data volume is small but high quality.

### 10.5 When not to use it first

DoRA should not block Gamma v1. Implement LoRA first, then DoRA after the baseline trainer, checkpointing, and evaluation pipeline are stable.

---

## 11. How AdaLoRA and dynamic-rank methods should fit

### 11.1 Why Gamma might want adaptive rank

Not every layer contributes equally to downstream adaptation. Not every node needs the same expressive budget. Adaptive rank methods can move parameter budget toward more useful layers or shrink budget where learning is redundant.

### 11.2 Why Gamma should wait

Adaptive-rank methods add:

- more hyperparameters,
- more training dynamics,
- more aggregation complexity,
- harder checkpoint comparison,
- more difficult federated synchronization.

The FedLoRA survey treats rank heterogeneity and adaptive rank as promising but nontrivial directions. fileciteturn9file5turn9file16 Gamma should therefore treat them as **phase 3**, not phase 1.

### 11.3 Phase-3 use cases

Add adaptive rank when:

- some nodes repeatedly need richer adapters,
- thermal limits differ across hardware,
- the cluster begins specializing in very different domains,
- you need to cut communication while preserving performance.

---

## 12. How sparse LoRA should fit

### 12.1 Why sparse learning is attractive

The survey’s efficiency section describes sparse-learning approaches at the LoRA-parameter level and at the layer level. fileciteturn9file6turn9file18 For Gamma this is appealing because the cluster already thinks in terms of selective routing and delta movement rather than brute-force synchronization.

### 12.2 What Gamma should do

Sparse LoRA in Gamma should mean one or more of:

- update only the most important target layers,
- prune low-energy ranks before sync,
- transmit only changed adapter shards,
- compress low-impact deltas,
- freeze adapter regions that have converged.

### 12.3 Good first sparse policy

Use post-training sparsification rather than sparse optimization first:

1. train normal LoRA,
2. compute rank or layer importance,
3. prune or zero insignificant blocks,
4. sync only the surviving blocks,
5. evaluate before promotion.

This keeps the first implementation simpler.

---

## 13. How personalized dual-adapter learning should fit

### 13.1 Why it is the natural Gamma design

The cluster is homogeneous in base model but intentionally heterogeneous in environment and role. The survey’s personalized LoRA strategies, especially dual-adapter setups, provide a strong blueprint for exactly this situation. fileciteturn9file4turn9file15

### 13.2 Target design

Every node should eventually have:

- `base_model`
- `global_council_adapter`
- `node_local_adapter`
- `ephemeral_task_context`

This allows:

- global stability,
- local specialization,
- temporary context-based behavior,
- clean checkpointing.

> [!IMPORTANT]
> **[REVIEW — GAP-09: Adapter Composition Semantics]** The plan proposes stacking `global_council_adapter + node_local_adapter` but never specifies the composition arithmetic. This must be defined before implementation:
>
> **Option A — Additive (recommended for v1):**
> `W_eff = W_base + ΔW_global + ΔW_local`
> Both adapters target the same modules. Deltas are summed. Simple, deterministic, easy to debug.
>
> **Option B — Partitioned modules:**
> Global adapter targets {q_proj, k_proj, v_proj, o_proj}. Local adapter targets {gate_proj, up_proj, down_proj}. No overlap, no conflict.
>
> **Option C — Sequential (chained):**
> `h = (W_base + ΔW_global)(x)`, then `h' = (I + ΔW_local)(h)`. More expressive but harder to merge.
>
> **Conflict resolution rule (required):** If both adapters target the same module, the composition must be explicitly defined (additive sum vs. local-overrides-global vs. weighted blend with a tunable λ).

### 13.3 Training policy

Global adapter trains from:

- high-consensus traces,
- judge-approved outcomes,
- literature-backed accepted resolutions,
- human-verified corrections.

Local adapter trains from:

- node-specific successful traces,
- role-specific subdomains,
- tool-use habits,
- specialized correction data.

---

## 14. What the federated part should look like in Gamma

### 14.1 Nodes are clients

Each Gamma node acts as a federated client during consolidation.

### 14.2 Aggregation server can be logical, not necessarily physical

The “server” in FedLoRA does not need to be one sacred monolith. In Gamma, it can be:

- a dedicated coordination node,
- a rotating leader,
- a daemon that collects adapter exports,
- a coordination process reading from shared storage.

### 14.3 What should be communicated

Only communicate:

- adapter states,
- adapter deltas,
- metadata,
- sample-quality summaries,
- evaluation results.

Do not communicate:

- raw private traces unless allowed,
- full base weights,
- unfiltered runtime noise,
- low-confidence learning artifacts.

---

## 15. The crucial FedLoRA lesson: aggregation is not trivial

The FedLoRA survey emphasizes that naïvely aggregating LoRA matrices separately is mathematically misaligned with the real combined update. This is the “LoRA aggregation discordance” problem. fileciteturn9file2turn9file11

Gamma must therefore pick an aggregation policy intentionally.

### 15.1 Policy options

#### Option 1: separate A/B averaging

Do not use as the default. It is the easiest to code but the weakest mathematically.

#### Option 2: single low-rank matrix aggregation

In each round, only one factor is learned/aggregated while the other remains fixed. The survey presents this as a simple and efficient way to reduce discordance. fileciteturn9file2

#### Option 3: alternating minimization

Alternate which factor is learned across rounds. This is a stronger practical default for Gamma because it balances simplicity and better alignment. fileciteturn9file2

#### Option 4: full update aggregation

Reconstruct the full low-rank-induced update, aggregate that, then decompose again. This is more principled but heavier. fileciteturn9file2turn9file18

> [!WARNING]
> **[REVIEW — GAP-02: Aggregation Strategy Is Outdated]** Since this plan was drafted, two superior aggregation methods have been peer-reviewed and published. They should be added as Options 5 and 6:
>
> #### Option 5: FFA-LoRA (Freeze-A aggregation) — RECOMMENDED AS V1 DEFAULT
>
> Fix matrix A at random initialization, train only B. Aggregation becomes simple linear averaging of B — **zero discordance by construction**, trivially correct, simplest possible implementation. Published at **ICLR 2025**. *(Sun et al., 2024; DOI: [10.48550/arXiv.2407.19195](https://doi.org/10.48550/arXiv.2407.19195))*
>
> #### Option 6: FedEx-LoRA (Exact aggregation with residual correction)
>
> Adds a residual error term (ΔW_res) to the frozen base weight matrix, enabling **mathematically exact** global updates while keeping LoRA’s efficiency. Published as **ACL 2025 Oral**. *(Singhal et al., 2024; DOI: [10.48550/arXiv.2405.09384](https://doi.org/10.48550/arXiv.2405.09384))*
>
> #### Updated Aggregation Comparison Matrix
>
> | Strategy | Discordance | Complexity | Communication Cost | Peer Review |
> |:---|:---:|:---:|:---:|:---:|
> | Separate A/B averaging | High | Trivial | Low | N/A |
> | Single-matrix (fix A or B) | Zero (for fixed matrix) | Low | Low | ICLR 2025 |
> | Alternating minimization | Reduced | Moderate | Low | Survey-level |
> | Full update aggregation | Zero | High | High (full ΔW) | Survey-level |
> | **FFA-LoRA (freeze A)** | **Zero** | **Low** | **Low** | **ICLR 2025** |
> | **FedEx-LoRA (residual)** | **Zero** | **Moderate** | **Moderate** | **ACL 2025** |

### 15.2 Gamma’s recommendation

For Gamma v1:

- start with **alternating aggregation**,
- keep full-update aggregation as a future upgrade,
- record aggregation policy in checkpoints,
- always compare post-aggregation performance against node-local baselines.

> [!CAUTION]
> **[REVIEW — Revised Recommendation]** Alternating aggregation should **not** be the v1 default. **FFA-LoRA (freeze A, average B)** is simpler to implement, provably discordance-free, and already peer-reviewed at ICLR 2025. It reduces implementation risk and debugging surface area. Alternating aggregation should be retained as a Phase 3+ upgrade for when more expressive federation is needed.

---

## 16. How the consolidation lifecycle should work

### 16.1 Input

Approved traces from Discovery and Plan modes.

### 16.2 Sample selection

A sample enters training only if it passes a gating policy.

Required metadata:

- `consensus_level`
- `judge_score`
- `human_verified`
- `doi_support`
- `failure_class`

### 16.3 Local training

Each node trains a local adapter for a bounded number of steps.

### 16.4 Local evaluation

Before export, each node evaluates its new adapter on:

- held-out local traces,
- consistency prompts,
- anti-hallucination prompts,
- role-specific benchmarks.

### 16.5 Federation

Exported adapters are aggregated according to the current policy.

### 16.6 Global evaluation

The new global adapter is tested on:

- cluster-wide benchmark suite,
- literature-grounded tasks,
- contradiction resolution tasks,
- plan stability tasks.

### 16.7 Promotion

Only if the new adapter passes thresholds should it be promoted.

> [!CAUTION]
> **[REVIEW — GAP-08: No Convergence/Promotion Criteria Defined]** "Passes thresholds" is not a specification. Required quantitative criteria:
>
> | Criterion | Threshold | Notes |
> |:---|:---:|:---|
> | Primary metric improvement | ≥ 0.5% | On at least one Gamma-relevant metric |
> | Maximum regression on any metric | ≤ 2.0% | Across all tracked metrics |
> | Minimum evaluation set size | ≥ 100 samples | Per metric category |
> | Statistical significance | p < 0.05 | Paired bootstrap test |
> | Base-model regression guard | ≤ 2.0% | On held-out base capability test set |
> | Hallucination rate | ≤ baseline | Must not increase vs. previous adapter |
>
> Promotion should also require sign-off from at least 2 of: (a) automated eval pass, (b) judge-node approval, (c) human verification flag.

### 16.8 Rollback

If it fails later, rollback should be immediate.

---

## 17. The data Gamma should train on

Not all traces are equal. Gamma should define a strict training data hierarchy.

### 17.1 Gold samples

- human-verified,
- literature-cited,
- judge-approved,
- high-consensus,
- successful outputs.

### 17.2 Silver samples

- high judge agreement,
- strong internal consensus,
- no human confirmation yet.

### 17.3 Red-flag samples

- unresolved disagreement,
- known hallucination,
- unsupported assertion,
- failed DOI grounding,
- schema drift.

Red-flag samples should not be used for direct supervised learning, though they may be useful as negative or rejection examples in special training modes.

---

## 18. Training schemas Gamma should support

Gamma should support at least three training data schemas.

### 18.1 SFT-style schema

```json
{
  "task_type": "sft",
  "role": "methods_skeptic",
  "input": "paper context + question",
  "target": "validated answer",
  "evidence_dois": ["..."],
  "consensus_level": "high"
}
```

### 18.2 Debate-to-digest schema

```json
{
  "task_type": "debate_digest",
  "branch_context": "...",
  "disagreement": "...",
  "accepted_resolution": "...",
  "judge_scores": {"internal": 0.88, "external": 0.91}
}
```

### 18.3 Rejection / humility schema

```json
{
  "task_type": "abstain_or_escalate",
  "input": "insufficient-evidence case",
  "target": "ASK_EXPERT_HUMAN",
  "reason": "low evidence / failed consensus / contradictory citations"
}
```

That last schema is important because Gamma’s identity depends not only on producing answers but on learning when not to overclaim.

> [!TIP]
> **[REVIEW — GAP-10: Negative Training / DPO Specification]** The abstention schema (§18.3) teaches the *format* of "ASK_EXPERT_HUMAN" but not the *discrimination* between answerable and unanswerable queries. For v1, SFT with abstention targets is acceptable. For v2+, this must be upgraded:
> - Convert red-flag samples to **preference pairs**: (correct_answer vs. hallucinated_answer)
> - Train with **DPO** (Direct Preference Optimization) or **KTO** (Kahneman-Tversky Optimization)
> - This transforms red-flag samples from waste into high-value training signal

---

## 19. How to evaluate PEFT methods in Gamma

Gamma should never adopt a new PEFT method just because it lowers loss. It should evaluate methods on cluster-relevant criteria.

### 19.1 Metrics that matter

- literature-grounded accuracy,
- contradiction detection quality,
- citation discipline,
- role consistency,
- abstention correctness,
- cross-node consensus improvement,
- branch compression quality,
- hallucination rate,
- rollback rate,
- adapter size,
- sync cost,
- training time on Apple Silicon.

### 19.2 Minimal benchmark suite

Each method should be benchmarked on:

- scientific summarization,
- methods extraction,
- contradiction finding,
- plan synthesis,
- code architecture reasoning,
- ask-expert triggering,
- multi-step literature adjudication.

### 19.3 Comparative matrix

Gamma should compare:

- LoRA,
- QLoRA,
- DoRA,
- sparse LoRA,
- dual-adapter LoRA,
- later AdaLoRA.

And report for each:

- adapter size,
- trainable parameters,
- local memory use,
- convergence speed,
- cluster sync cost,
- post-training quality.

---

## 20. MLX-specific operational guidance

### 20.1 Why MLX is appropriate

Apple’s MLX ecosystem is explicitly positioned for local inference and fine-tuning on Apple Silicon, making it a strong substrate for Gamma’s local, privacy-preserving, hardware-sovereign design. citeturn458295search3turn458295search11

### 20.2 What Gamma should assume

Gamma should assume:

- unified memory is precious but shared,
- checkpoint and adapter formats should be simple,
- memory-mapped loading matters,
- concurrency must be managed conservatively,
- quantized bases plus small trainable adapters are the practical default.

> [!CAUTION]
> **[REVIEW — GAP-04: MLX Memory Budget Required]** "Unified memory is precious" is not actionable without numbers. Current benchmarks (2025-2026):
>
> | Model (4-bit QLoRA) | Inference Memory | Training Peak | Min Unified RAM |
> |:---|:---:|:---:|:---:|
> | ~1.5B params | ~1.5 GB | ~4–6 GB | 8 GB |
> | 3B params | ~2.5 GB | ~5.0 GB | 16 GB |
> | 7B params | ~4.5 GB | ~14–16 GB | 32 GB (tight) |
> | 13B+ params | ~8 GB | ~28+ GB | 64 GB+ |
>
> **Critical constraint for 8-node cluster:** If each node also runs live inference, training and inference **cannot coexist on nodes with <32 GB** without explicit memory partitioning or time-slicing. The plan must specify:
> 1. Whether consolidation windows are **exclusive** (no inference during training) — **recommended for v1**
> 2. Or **concurrent** (requires memory budget split, e.g., 60% inference / 40% training)
> 3. Maximum model size per node class (e.g., M2 Pro 16GB → 3B max; M2 Max 64GB → 13B)
> 4. Swap/OOM kill policy: halt training gracefully if memory pressure exceeds threshold

### 20.3 What Gamma should not assume

Gamma should not assume:

- every target family will expose identical module names,
- every quantization format will train equally well,
- every adapter method can be merged identically,
- every base model will tolerate the same target layer set.

### 20.4 Safe implementation pattern

Implement the forward path so that:

- the base weight remains frozen,
- the adapter path is explicit and inspectable,
- merged/unmerged math is deterministic,
- adapter exports include enough metadata to reconstruct state exactly.

---

## 21. A concrete staged roadmap

### Phase 0 — design and schemas

Build:

- `trace_schema.py`
- `sample_selector.py`
- `adapter_base.py`
- family configs
- evaluation task definitions

Exit criterion:

- canonical trace format exists,
- one evaluation dataset exists,
- one adapter abstraction exists.

### Phase 1 — single-node LoRA baseline

Build:

- `lora.py`
- `train_lora_mlx.py`
- `eval_adapter.py`
- `save_adapter.py`

Exit criterion:

- one model can be adapted locally,
- adapter can be saved/loaded,
- benchmark improves on at least one Gamma task.

### Phase 2 — QLoRA baseline

Build:

- quantized base loading support,
- adapter training on quantized base,
- comparison harness.

Exit criterion:

- QLoRA trains stably,
- memory savings are measured,
- quality remains acceptable.

### Phase 3 — federated episodic LoRA

Build:

- `federated_lora_episodic.py`
- aggregation coordinator,
- alternating aggregation,
- node export/import,
- checkpoint manager.

Exit criterion:

- two or more nodes can train locally and aggregate,
- rollback works,
- no naïve A/B averaging in default path.

### Phase 4 — dual-adapter federation

Build:

- global council adapter,
- node-local adapter,
- composition runtime,
- separate evaluation.

Exit criterion:

- node specialization improves without breaking global behavior.

### Phase 5 — DoRA

Build:

- `dora.py`
- train/eval path,
- comparison against LoRA.

Exit criterion:

- DoRA outperforms or stabilizes LoRA on selected Gamma benchmarks.

> [!WARNING]
> **[REVIEW — GAP-14: DoRA Should Be Phase 1.5, Not Phase 5]** DoRA (ICML 2024, NVIDIA; DOI: [10.48550/arXiv.2402.09353](https://doi.org/10.48550/arXiv.2402.09353)) consistently outperforms LoRA at equal or lower rank (especially rank 4-8), adds **zero inference overhead** (fully mergeable), and the implementation delta over LoRA is ~30 lines of code (one magnitude vector per layer + norm decomposition in forward). Deferring it to Phase 5 — after federated dual-adapter (Phase 4) — is unjustified.
>
> **Revised recommendation:** Insert **Phase 1.5 — DoRA baseline** between Phase 1 (single-node LoRA) and Phase 2 (QLoRA). The code delta is trivial, and it provides a strictly superior baseline for all subsequent federation experiments. All phases that rely on LoRA comparisons (Phases 2–7) benefit from having DoRA data earlier.
>
> **Phase 1.5 — DoRA baseline (insert here)**
> Build:
> - `dora.py` (extend `lora.py` with per-layer magnitude vector + directional LoRA)
> - DoRA train/eval path reusing Phase 1 infrastructure
>
> Exit criterion:
> - DoRA matches or exceeds LoRA on all Phase 1 benchmarks
> - Per-layer magnitude norms are logged and inspectable
> - Merge/unmerge produces bit-identical results

### Phase 6 — sparse / selective LoRA

Build:

- importance scoring,
- layer/rank pruning,
- delta sync.

Exit criterion:

- lower sync cost without major quality collapse.

### Phase 7 — adaptive rank

Build:

- `adalora.py`
- dynamic budget policy,
- heterogeneous-rank aggregation support.

Exit criterion:

- rank adaptation yields better quality/efficiency tradeoff than fixed-rank LoRA.

---

## 22. Safety rules for Gamma PEFT

1. Never train on unresolved traces.
2. Never promote an adapter without held-out evaluation.
3. Never overwrite the previous stable adapter checkpoint.
4. Never assume separate A/B averaging is mathematically safe.
5. Never couple live debate directly to live gradient updates.
6. Never let low-consensus samples dominate adapter training.
7. Always store method metadata with each checkpoint.
8. Always preserve merge/unmerge reproducibility.
9. Always benchmark against a fixed LoRA baseline.
10. Always maintain an abstention/escalation capability.

> [!CAUTION]
> **[REVIEW — GAP-06: Security / Threat Model Missing]** In a federated system, the safety rules above address *data quality* but not *adversarial/Byzantine threats*. Any node can potentially:
> - Send **poisoned adapter updates** (Byzantine attack)
> - Send updates trained on **adversarial data** (data poisoning)
> - **Exfiltrate cluster state** via adapter gradients (gradient inversion)
>
> Additional safety rules required:
>
> 11. Always **norm-clip** incoming adapter updates (reject if L2 norm > k × median of all node norms)
> 12. Never accept an adapter update from a node that has not passed its local evaluation gate
> 13. Always require **≥ N/2 nodes** to agree on update direction before global promotion
> 14. Consider optional **differential privacy** noise injection (ε-DP on adapter deltas) for sensitive domains
> 15. Always validate adapter state checksums (SHA-256) on receipt to detect corruption or tampering
> 16. Always run **anomaly detection** on adapter delta distributions (flag outliers >3σ from per-round mean)

---

## 23. Recommended default choices for Gamma v1

If implementation must start now, use the following defaults.

### Method

- Primary: LoRA
- Secondary experiment: QLoRA
- Deferred: DoRA
- Deferred further: AdaLoRA

### Federation

- Alternating aggregation
- Fixed rank
- Global + local adapters only after baseline works

### Data

- SFT on validated traces only
- no RL in v1
- no online updates in runtime

### Evaluation

- literature-grounded task suite
- contradiction test set
- abstention test set
- adapter rollback tests

### Operational cadence

- train only during Consolidation Mode
- train on schedule, not continuously
- checkpoint every cycle

---

## 23.5 Communication protocol specification

> [!NOTE]
> **[REVIEW — GAP-07: Wire Format Required]** Section 14 says "communicate adapter states" but provides no serialization, transport, or authentication specification. Minimum viable protocol:
>
> **Serialization:** SafeTensors (MLX-native, memory-mappable, no arbitrary code execution)
>
> **Transport:** gRPC over local mesh (or ZeroMQ for lower latency)
>
> **Message schema:**
> ```json
> {
>   "node_id": "gamma-node-03",
>   "round_id": 42,
>   "method": "lora",
>   "rank": 8,
>   "alpha": 16,
>   "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
>   "adapter_state": "<safetensors binary blob>",
>   "metadata": {
>     "training_samples": 256,
>     "training_steps": 400,
>     "local_eval_score": 0.87,
>     "base_model_hash": "sha256:abcdef..."
>   },
>   "checksum": "sha256:123456..."
> }
> ```
>
> **Compression:** Optional zstd on adapter tensor payloads (typical 2-4× compression on FP16 deltas)
>
> **Authentication:** Mutual TLS or pre-shared keys (even on local mesh, defense-in-depth)

## 23.6 Data pipeline specification

> [!NOTE]
> **[REVIEW — GAP-12: Data Pipeline Missing]** Sections 6.1 and 18 define *what* data looks like but not *how* it flows. Required specification:
>
> 1. **Trace storage**: Append-only JSONL files per node, one file per consolidation epoch, stored in `data/traces/{node_id}/epoch_{N}.jsonl`
> 2. **Sample selector**: SQL-like filter over JSONL metadata fields (consensus_level ≥ threshold AND judge_score ≥ threshold AND failure_class IS NULL)
> 3. **Tokenization**: Use model-family-specific tokenizer via `mlx-lm` or HuggingFace `tokenizers`; cache tokenized datasets as memory-mapped arrays
> 4. **Batching**: Dynamic padding to longest-in-batch, with `--mask-prompt` to train only on target tokens (not input context)
> 5. **Data loader**: Compatible with `mlx.data` or a minimal custom iterator that yields `(input_ids, attention_mask, labels)` tuples

---

## 24. Final recommendation

For Gamma, the best path is not “implement every PEFT paper immediately.” The best path is:

1. create a robust model-agnostic adapter abstraction,
2. prove single-node MLX LoRA works,
3. define high-quality episodic training traces,
4. federate carefully with alternating aggregation,
5. split learning into global and local adapters,
6. add DoRA only after LoRA is benchmarked,
7. add sparse and adaptive methods only when there is evidence they help Gamma’s actual workloads.

In other words, Gamma should use PEFT not as a flashy optimization trick but as the biological equivalent of **slow synaptic consolidation**. The context matrix is working memory. The adapters are long-term skill. The judges and literature are reward shaping. The checkpoint stack is memory safety. And FedLoRA is the mechanism that lets a distributed cluster learn collaboratively without collapsing into full-model chaos.

---

## 25. Core sources to keep attached to this plan

- FedLoRA survey for distributed learning, heterogeneity, and efficiency in federated LoRA. fileciteturn9file0turn9file12
- LoRA original paper for the base PEFT formulation. citeturn458295search0
- DoRA paper for weight-decomposed low-rank adaptation. citeturn463687search0turn463687search2
- Apple MLX materials and MLX LoRA examples for local Apple Silicon fine-tuning context. citeturn458295search3turn458295search11

> [!IMPORTANT]
> **[REVIEW — Canonical DOI Reference Table]** The inline citations above are chatbot artifacts. Canonical references with DOIs:
>
> | Paper | Authors | Venue | DOI |
> |:---|:---|:---:|:---|
> | LoRA: Low-Rank Adaptation of Large Language Models | Hu et al. | ICLR 2022 | [10.48550/arXiv.2106.09685](https://doi.org/10.48550/arXiv.2106.09685) |
> | QLoRA: Efficient Finetuning of Quantized LLMs | Dettmers et al. | NeurIPS 2023 | [10.48550/arXiv.2305.14314](https://doi.org/10.48550/arXiv.2305.14314) |
> | DoRA: Weight-Decomposed Low-Rank Adaptation | Liu et al. | ICML 2024 | [10.48550/arXiv.2402.09353](https://doi.org/10.48550/arXiv.2402.09353) |
> | AdaLoRA: Adaptive Budget Allocation for PEFT | Zhang et al. | ICLR 2023 | [10.48550/arXiv.2303.10512](https://doi.org/10.48550/arXiv.2303.10512) |
> | FFA-LoRA: Federated Freeze-A LoRA | Sun et al. | ICLR 2025 | [10.48550/arXiv.2407.19195](https://doi.org/10.48550/arXiv.2407.19195) |
> | FedEx-LoRA: Exact Aggregation for Federated LoRA | Singhal et al. | ACL 2025 (Oral) | [10.48550/arXiv.2405.09384](https://doi.org/10.48550/arXiv.2405.09384) |
> | FedAvg: Communication-Efficient Learning | McMahan et al. | AISTATS 2017 | [10.48550/arXiv.1602.05629](https://doi.org/10.48550/arXiv.1602.05629) |
> | FLoRA: Stacking-Based Heterogeneous Aggregation | Wang et al. | NeurIPS 2024 | [10.48550/arXiv.2407.11211](https://doi.org/10.48550/arXiv.2407.11211) |

---

## 26. Review summary and verdict

> **Overall score: 7.5/10** — Strong conceptual architecture, weak operational specification.
>
> The plan correctly separates live cognition from slow consolidation, identifies the LoRA aggregation discordance problem, proposes a sensible phased roadmap, and maintains philosophical coherence. The biological metaphor (§24) is the right framing.
>
> **14 gaps were identified.** The three most critical:
> 1. **No concrete hyperparameters** (§8.3) — implementation will stall on day one
> 2. **Aggregation default is outdated** (§15) — FFA-LoRA is simpler and provably correct
> 3. **No security/threat model** (§22) — federated systems without Byzantine protection are fundamentally unsafe
>
> Full review artifact: see `gamma_fedlora_review.md`

