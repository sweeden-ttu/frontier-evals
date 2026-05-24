#!/usr/bin/env bash
# Generate Rogii ML pipelines + Slurm submit wrappers from frontier.yaml across agent-* worktrees.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}/project/paperbench"
uv sync -q
uv run python -m paperbench.scripts.generate_rogii_pipelines --all "$@"
