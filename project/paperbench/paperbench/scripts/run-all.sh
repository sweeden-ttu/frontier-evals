
bash /lustre/work/sweeden/frontier-evals/scripts/generate_rogii_worktree_pipelines.sh

# Preview Slurm commands (no submit)
DRY_RUN=0 bash /lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii/generated/submit_all_variants.sh

# Submit one variant from its worktree
bash /lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii/generated/submit_typewell.sh

# Submit all six (respects squeue — skips active jobs)
bash /lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii/generated/submit_all_variants.sh --submit

# Or via Python directly
cd /lustre/work/sweeden/frontier-evals/project/paperbench
uv run python -m paperbench.scripts.generate_rogii_pipelines --all --submit