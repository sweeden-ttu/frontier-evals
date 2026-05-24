# Experiment descriptor: parallel_multiwell_loader

**Approach:** Parallel IO + geology surfaces

## Base paper (ablation / experiment design)

- **Title:** Dask: Parallel Computation with Blocked algorithms and Task Scheduling
- **Authors:** Rocklin
- **Year / venue:** 2015 / SciPy proceedings
- **URL:** https://conference.scipy.org/proceedings/scipy2015/matthew_rocklin.html

**Claims driving ablations:**
- Parallel blocked IO scales multi-well CSV ingestion beyond single-threaded loaders.
- Worker count and on-disk cache are ablatable throughput–memory tradeoffs.
- Geology surface columns add Type-1 feature materialization cost testable via on/off ablation.

**Ablation-relevant sections:** §2 task graph, §3 scheduling

## Trace theory paper (agent audit layer)

- **PaperBench id:** `agent-tracing`
- **Title:** Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents
- **Sections:** sec/7 Bayesian loop, sec/4 evaluation audit
- **Role:** trace_language_audit_and_agent_implementation

## Agent implementation (`trace_language.csv`)

- **Path:** `traces/preprocessing/parallel_multiwell_loader/trace_language.csv`
- **Resource envelopes:** rows 2-21
- **Orchestrator:** `paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator`

## Experiment linkage

- **Hypothesis:** Parallel IO + geology surfaces improves competition RMSE (post-PS) vs shared baseline under nested GroupKFold, as motivated by Rocklin (2015).
- **Primary metric:** rmse_post_ps
- **Ablation plan:** `ablation_plan.json`
- **Subdivision:** `subdivision_manifest.json`
- **Machine-readable descriptor:** `experiment_descriptor.json`
