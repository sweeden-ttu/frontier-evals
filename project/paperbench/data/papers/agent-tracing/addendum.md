# Agent-Tracing Replication Addendum

## Source repository

- Paper LaTeX: `/lustre/work/sweeden/agent-tracing/src/`
- GitHub: https://github.com/sweeden-ttu/agent-tracing

## Rogii trace language examples

Canonical template:

```
/lustre/work/sweeden/rogii/trace_language.csv
```

Six preprocessing variants (PaperBench grading fixtures):

```
/lustre/work/sweeden/rogii/traces/preprocessing/
  baseline_column_transformer/trace_language.csv
  typewell_gr_alignment/trace_language.csv
  ps_point_leakage_aware/trace_language.csv
  robust_scale_log1p/trace_language.csv
  parallel_multiwell_loader/trace_language.csv
  formation_plane_spatial/trace_language.csv
```

Each file has **20 swim-lane columns** (agent roles). Rows 2–4 are governance (`pin_seed`, `add_task`/`add_dep`, `topological_order`). Row 5 is `dispatch`. Remaining rows are single-action tokens or copy-pasteable CLI commands.

## CLI-for-agents conventions

Cells should be runnable shell commands where appropriate:

```bash
kaggle --version
cd /lustre/work/sweeden/rogii && kaggle competitions download -c rogii-wellbore-geology-prediction -p data/ -q
cd /lustre/work/sweeden/rogii && sbatch --parsable hpcc/train_tcn.slurm
uv pip install lightgbm -q
```

## Chomsky / PaperBench integration

- Architecture spec: `frontier.yaml` at repo root
- Implementation package: `paperbench/chomsky/`
- Contracts output: `paperbench/chomsky/contracts/`

Run local validation (no Docker required):

```bash
cd /lustre/work/sweeden/frontier-evals/project/paperbench
uv run python -m paperbench.scripts.implement_agent_tracing --validate-traces
```

## Competition context

- Kaggle: `rogii-wellbore-geology-prediction`
- Target: `TVT` beyond Prediction Start
- Per-well horizontal + typewell CSVs

## Submission layout

Your submission should include:

```
submission/
  reproduce.sh
  chomsky/
    classify.py          # emits chomsky_classification_v1
    verify.py            # emits verification_report_v1
    trace_validate.py    # CSV schema checks
  traces/                # copy or symlink Rogii variants
  README.md              # mapping implementations → schemata
```

`reproduce.sh` must run trace validation and print classifier summaries for all six variants.
