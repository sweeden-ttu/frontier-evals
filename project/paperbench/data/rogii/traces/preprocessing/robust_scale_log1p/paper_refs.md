# Experiment descriptor: robust_scale_log1p

**Approach:** RobustScaler + log1p target

## Base paper (ablation / experiment design)

- **Title:** Robust Statistics: The Approach Based on Influence Functions
- **Authors:** Hampel, Ronchetti, Rousseuw, Stahel
- **Year / venue:** 1986 / Wiley
- **DOI:** 10.1002/9781118186435
- **URL:** https://onlinelibrary.wiley.com/doi/book/10.1002/9781118186435

**Claims driving ablations:**
- Robust location/scale estimators reduce outlier sensitivity vs ordinary standardization.
- log1p target transform stabilizes skewed well-log regression residuals.
- Inverse transform at predict time is an ablatable factor coupling train and inference stacks.

**Ablation-relevant sections:** Ch. 2 influence functions, Ch. 5 M-estimators

**Supporting references:**
- Pedregosa et al. (2011). *Scikit-learn: Machine Learning in Python* — RobustScaler implementation reference

## Trace theory paper (agent audit layer)

- **PaperBench id:** `agent-tracing`
- **Title:** Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents
- **Sections:** sec/3 Type-1 linear transcript
- **Role:** trace_language_audit_and_agent_implementation

## Agent implementation (`trace_language.csv`)

- **Path:** `traces/preprocessing/robust_scale_log1p/trace_language.csv`
- **Resource envelopes:** rows 2-21
- **Orchestrator:** `paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator`

## Experiment linkage

- **Hypothesis:** RobustScaler + log1p target improves competition RMSE (post-PS) vs shared baseline under nested GroupKFold, as motivated by Hampel, Ronchetti, Rousseuw, Stahel (1986).
- **Primary metric:** rmse_post_ps
- **Ablation plan:** `ablation_plan.json`
- **Subdivision:** `subdivision_manifest.json`
- **Machine-readable descriptor:** `experiment_descriptor.json`
