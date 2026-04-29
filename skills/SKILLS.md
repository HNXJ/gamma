# Gamma Paper-Anchored Skill Architecture

This document defines the formal library of reusable scientific skills for the Gamma Council. These skills are anchored in the **visual grammar**, **metric ontology**, and **objective scaffolding** of the foundational scientific paper (HN et al., 2026).

## 🏛️ The Skill Promotion Rule
**Goal:** Transition from ephemeral scripts to a stable, accumulating neuroscience toolkit.

When an agent writes code that successfully produces a validated artifact, it should propose a reusable skill skeleton from that success. A script is eligible for promotion if it satisfies the following **Promotion Test**:
1. **Successful Execution:** The code ran successfully at least once on the real runtime.
2. **Structural Validity:** The output artifact is structurally valid (e.g., non-empty JSON/PNG).
3. **Reusability:** The code is modular and reusable across more than one task.
4. **Strict Typing:** Inputs and outputs are clearly typed.
5. **Paper Alignment:** The result matches one of the paper's figure or metric patterns.

## 📊 Tier 1: Paper-Anchored Readout Skills (Visual Grammar)
These skills enforce the visual grammar and consistent reporting of model responses.

### 1. `skill_psd_band_report`
- **Pattern:** Fig. 4/5 (PSD panels).
- **Purpose:** Report power in specific bands (Delta, Beta, Gamma).

### 2. `skill_raster_psth_bundle`
- **Pattern:** Fig. 3/7 (Raster/PSTH motifs).
- **Purpose:** Produce high-fidelity spike timing visualizations.

### 3. `skill_pre_post_figure_pack`
- **Pattern:** Pre/Post comparison panels used throughout paper.
- **Purpose:** Visualize the effect of optimization on dynamics.

### 4. `skill_loss_curve_with_parameter_table`
- **Pattern:** Fig. 2/4 (Optimization traces).
- **Purpose:** Report loss convergence alongside final parameter values.

### 5. `skill_model_vs_data_spectrogram_compare`
- **Pattern:** Fig. 8 (Spectrotemporal comparisons).
- **Purpose:** Qualitative and quantitative comparison of model vs. reference data.

## 🧬 Tier 2: Objective-Definition Skills (Metric Ontology)
These skills define targets and evaluation metrics in the paper's language.

### 1. `skill_target_firing_rate_ei`
- **Target:** 20 spikes/s (E), 70 spikes/s (I).
- **Metric:** Firing rate MSE.

### 2. `skill_target_natural_frequency`
- **Target:** Peak power at 30 Hz.
- **Metric:** Natural frequency deviation.

### 3. `skill_target_synchronization_index`
- **Pattern:** game001 Proponent Sweep.
- **Purpose:** Kuramoto order parameter R for coupling-strength analysis.

### 4. `skill_target_beta_gamma_push_pull`
- **Target:** Band dominance shift across conditions.
- **Metric:** Beta/Gamma power ratio.

### 5. `skill_target_contextual_gain_shift`
- **Target:** Top-down gain modulation (Fig. 6).
- **Metric:** Gain ratio across inputs.

## 🚀 Tier 3: Promotion & Lifecycle
- **`promotion_from_successful_run`**: The master skill used by agents to draft new skills based on the Promotion Test.

---
*Reference Paper: HN et al. (2026) - Generalized Slow-Learning Discovery and Reporting (GSDR).*
