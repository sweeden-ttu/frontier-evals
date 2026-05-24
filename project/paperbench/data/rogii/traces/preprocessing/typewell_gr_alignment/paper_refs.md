# Experiment descriptor: typewell_gr_alignment

**Approach:** GR/typewell alignment features

## Base paper (ablation / experiment design)

- **Title:** Dynamic Programming Algorithm Optimization for Spoken Word Recognition
- **Authors:** Sakoe, Chiba
- **Year / venue:** 1978 / IEEE Trans. Acoustics, Speech, and Signal Processing
- **DOI:** 10.1109/TASSP.1978.1163055
- **URL:** https://ieeexplore.ieee.org/document/1163055

**Claims driving ablations:**
- DTW aligns sequences with local warping—applicable to depth-indexed GR/typewell curves.
- Interpolation choice (linear vs PCHIP) changes tie-point smoothness and physics baseline RMSE.
- Typewell alignment is an inductive bias ablation: off vs on tests geologic transfer value.

**Ablation-relevant sections:** §2 warping path, §3 band constraints

**Supporting references:**
- Rider, Kennedy (2011). *The Geological Interpretation of Well Logs* — Typewell / gamma-ray correlation domain vocabulary

## Trace theory paper (agent audit layer)

- **PaperBench id:** `agent-tracing`
- **Title:** Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents
- **Sections:** sec/3 Type-2 stack, sec/7 R&D Bayesian loop
- **Role:** trace_language_audit_and_agent_implementation

## Agent implementation (`trace_language.csv`)

- **Path:** `traces/preprocessing/typewell_gr_alignment/trace_language.csv`
- **Resource envelopes:** rows 2-21
- **Orchestrator:** `paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator`

## Experiment linkage

- **Hypothesis:** GR/typewell alignment features improves competition RMSE (post-PS) vs shared baseline under nested GroupKFold, as motivated by Sakoe, Chiba (1978).
- **Primary metric:** rmse_post_ps
- **Ablation plan:** `ablation_plan.json`
- **Subdivision:** `subdivision_manifest.json`
- **Machine-readable descriptor:** `experiment_descriptor.json`
