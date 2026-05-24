# Experiment descriptor: ps_point_leakage_aware

**Approach:** PS-point detection + post-PS RMSE mask

## Base paper (ablation / experiment design)

- **Title:** Leakage in Data Mining: Formulation, Detection, and Avoidance
- **Authors:** Kaufman, Rosset, Perlich, Stitelman
- **Year / venue:** 2012 / ACM TKDD
- **DOI:** 10.1145/2382575.2382577
- **URL:** https://doi.org/10.1145/2382575.2382577

**Claims driving ablations:**
- Train-test leakage inflates offline metrics; evaluation masks must match deployment horizon.
- Post-perforation-start (PS) RMSE is the competition-relevant subset—full-well eval is optimistic.
- Strict vs lenient TVT input audits are ablatable governance gates (Type-3 consumers).

**Ablation-relevant sections:** §3 leakage taxonomy, §5 detection strategies

## Trace theory paper (agent audit layer)

- **PaperBench id:** `agent-tracing`
- **Title:** Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents
- **Sections:** sec/4 audit protocol, sec/5 limitations
- **Role:** trace_language_audit_and_agent_implementation

## Agent implementation (`trace_language.csv`)

- **Path:** `traces/preprocessing/ps_point_leakage_aware/trace_language.csv`
- **Resource envelopes:** rows 2-21
- **Orchestrator:** `paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator`

## Experiment linkage

- **Hypothesis:** PS-point detection + post-PS RMSE mask improves competition RMSE (post-PS) vs shared baseline under nested GroupKFold, as motivated by Kaufman, Rosset, Perlich, Stitelman (2012).
- **Primary metric:** rmse_post_ps
- **Ablation plan:** `ablation_plan.json`
- **Subdivision:** `subdivision_manifest.json`
- **Machine-readable descriptor:** `experiment_descriptor.json`
