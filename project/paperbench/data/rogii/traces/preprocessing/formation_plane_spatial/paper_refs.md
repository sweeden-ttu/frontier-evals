# Experiment descriptor: formation_plane_spatial

**Approach:** Drilling geometry + formation KNN

## Base paper (ablation / experiment design)

- **Title:** Nearest Neighbor Pattern Classification
- **Authors:** Cover, Hart
- **Year / venue:** 1967 / IEEE Trans. Information Theory
- **DOI:** 10.1109/TIT.1967.1053964
- **URL:** https://ieeexplore.ieee.org/document/1053964

**Claims driving ablations:**
- k-NN risk bounds motivate formation-label propagation from spatial neighbors in TVD/MD space.
- Drilling geometry features encode directional survey context for plane-aware lithology.
- Formation plane fit (off/on) ablates explicit structural surface vs pure neighbor voting.

**Ablation-relevant sections:** §1 k-NN error bounds, §2 finite-sample behavior

**Supporting references:**
- Shepard (1968). *A Two-Dimensional Interpolation Function for Irregularly-Spaced Data* — Formation surface / plane interpolation analogue

## Trace theory paper (agent audit layer)

- **PaperBench id:** `agent-tracing`
- **Title:** Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents
- **Sections:** sec/3 Type-0 envelope
- **Role:** trace_language_audit_and_agent_implementation

## Agent implementation (`trace_language.csv`)

- **Path:** `traces/preprocessing/formation_plane_spatial/trace_language.csv`
- **Resource envelopes:** rows 2-21
- **Orchestrator:** `paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator`

## Experiment linkage

- **Hypothesis:** Drilling geometry + formation KNN improves competition RMSE (post-PS) vs shared baseline under nested GroupKFold, as motivated by Cover, Hart (1967).
- **Primary metric:** rmse_post_ps
- **Ablation plan:** `ablation_plan.json`
- **Subdivision:** `subdivision_manifest.json`
- **Machine-readable descriptor:** `experiment_descriptor.json`
