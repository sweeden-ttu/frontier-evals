# Judge addendum: agent-tracing

Grade **Code Development** tasks by inspecting the submission tree. Do not require GPU training or live Kaggle submission for full credit on trace/Chomsky tasks.

## Trace CSV rubric hints

- **20 columns:** header row must match Rogii canonical agent names.
- **Governance rows 2–4:** may contain multiple non-empty cells (exception to single-cell rule).
- **Single-action rows:** at most one non-empty cell per data row (row ≥ 5).
- **Closure:** pipeline ends with dependency-graph tokens (`record`, `serialize_markdown`, `topological_order` or equivalent).
- **CLI cells:** `kaggle`, `sbatch`, `uv`, `cd`, `find` commands count as Type-0 envelope evidence.

## Chomsky classification

Accept `chomsky_classification_v1` JSON with fields: `agent_id`, `predicted_chomsky_class`, `sigma_trace_alphabet_encoding`, `structural_witnesses`, `memory_hypothesis`.

Rogii multi-agent pipelines with external CLI/subprocess calls should be classified **at least Type-0** at the envelope level unless a finite abstraction is proved.

## Partial credit

- Trace validator without classifier: credit schema tasks only.
- Classifier without six variants: credit per-variant proportionally.
