#!/usr/bin/env bash
# Local CI gate: chomsky + orchestrator dry-run for all six trace variants.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/project/paperbench"
uv sync -q
uv run pytest tests/unit/chomsky tests/unit/trace_pipeline -q
uv run python -m paperbench.scripts.implement_agent_tracing --validate-traces
for v in baseline_column_transformer typewell_gr_alignment ps_point_leakage_aware robust_scale_log1p parallel_multiwell_loader formation_plane_spatial; do
  uv run python -m paperbench.trace_pipeline.orchestrator --variant "$v" --dry-run >/dev/null
  echo "dry-run OK: $v"
done
echo "All trace pipeline CI checks passed."
