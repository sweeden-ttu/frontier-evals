# Experiment descriptor: baseline_column_transformer

**Approach:** ColumnTransformer + LightGBM baseline
**Branch:** `trace/baseline-column-transformer`
**PR:** #17

## Base papers (ablation / experiment design)

### 1. LightGBM: A Highly Efficient Gradient Boosting Decision Tree

- **Role:** model_experiment_descriptor
- **Authors:** Ke et al.
- **Year / venue:** 2017 / NeurIPS
- **DOI:** 10.5555/3294996.3295074
- **URL:** https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree

**Claims driving ablations:**
- Histogram-based GBDT improves tabular regression speed and accuracy vs level-wise boosting.
- Leaf-wise growth with regularization supports strong baselines on heterogeneous numeric features.
- Pairs with heterogeneous column preprocessing (ColumnTransformer) on tabular well-log features.

**Ablation-relevant sections:** §3 histogram algorithm, §4 experiments on dense numeric features

**Trace tokens:** `set_objective_regression, set_metric_rmse, log_best_iteration, train_with_seed_42`

### 2. Scikit-learn: Machine Learning in Python

- **Role:** preprocessing_experiment_descriptor
- **Authors:** Pedregosa et al.
- **Year / venue:** 2011 / JMLR
- **DOI:** 10.5555/1953048.2029494
- **URL:** https://jmlr.org/papers/v12/pedregosa11a.html

**Claims driving ablations:**
- ColumnTransformer applies disjoint transformers to heterogeneous column blocks.
- Pipeline compose chains preprocessing and estimator for leak-safe CV.
- numeric_scaler ablation (standard vs robust) maps to sklearn preprocessor choice.

**Ablation-relevant sections:** §2 unified API, ColumnTransformer / Pipeline compose

**Trace tokens:** `build_numeric_pipeline, build_lowcard_pipeline, build_highcard_pipeline, assemble_column_transformer`

## Trace theory paper (agent audit layer)

- **PaperBench id:** `agent-tracing`
- **Title:** Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents
- **Sections:** sec/2 agent schemata, sec/4 evaluation audit protocol
- **Role:** trace_language_audit_and_agent_implementation

## Agent implementation (`trace_language.csv`)

- **Path:** `traces/preprocessing/baseline_column_transformer/trace_language.csv`
- **Resource envelopes:** rows 2-21
- **Orchestrator:** `paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator`

## Experiment linkage

- **Hypothesis:** ColumnTransformer + LightGBM baseline improves competition RMSE (post-PS) vs shared baseline under nested GroupKFold, as motivated by Ke et al. (2017), Pedregosa et al. (2011).
- **Primary metric:** rmse_post_ps
- **Ablation plan:** `ablation_plan.json`
- **Subdivision:** `subdivision_manifest.json`
- **Machine-readable descriptor:** `experiment_descriptor.json`
