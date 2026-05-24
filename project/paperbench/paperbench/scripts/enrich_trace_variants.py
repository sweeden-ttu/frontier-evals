#!/usr/bin/env python3
"""Enrich each preprocessing variant with plan artifacts and notebooks."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/lustre/work/sweeden/frontier-evals/project/paperbench")
from paperbench.trace_pipeline.notebook_gen import generate_all_phase_notebooks

ROGII = Path("/lustre/work/sweeden/rogii/traces/preprocessing")
VARIANTS = [
    "baseline_column_transformer",
    "typewell_gr_alignment",
    "ps_point_leakage_aware",
    "robust_scale_log1p",
    "parallel_multiwell_loader",
    "formation_plane_spatial",
]
APPROACH = {
    "baseline_column_transformer": "ColumnTransformer + LightGBM baseline",
    "typewell_gr_alignment": "GR/typewell alignment features",
    "ps_point_leakage_aware": "PS-point detection + post-PS RMSE mask",
    "robust_scale_log1p": "RobustScaler + log1p target transform",
    "parallel_multiwell_loader": "Parallel IO + geology surface columns",
    "formation_plane_spatial": "Formation plane KNN spatial features",
}


def enrich_variant(slug: str) -> None:
    root = ROGII / slug
    root.mkdir(parents=True, exist_ok=True)
    plan = {
        "variant": slug,
        "approach": APPROACH[slug],
        "phases": [
            "01_data_analysis",
            "02_statistical_framework",
            "03_feature_engineering",
            "04_model_training",
            "05_evaluation",
            "06_submission",
        ],
        "agents": {
            "data": "eda_profiler",
            "plan": "experiment-design-architect",
            "model": "model_trainer",
            "eval": "oof_evaluator",
            "submit": "kaggle_submitter",
            "type3_consumer": "schema-sentinel",
        },
        "metric": "rmse",
        "smre": "mean_rmse_plus_std_across_folds",
    }
    (root / "mle_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (root / "statistical_framework.md").write_text(
        f"# Statistical framework: {slug}\n\n"
        f"**Approach:** {APPROACH[slug]}\n\n"
        "- **Hypothesis:** preprocessing variant improves OOF RMSE vs baseline.\n"
        "- **CV:** GroupKFold by well; nested subdivisions by well and depth bin.\n"
        "- **Metric:** competition RMSE; SMRE = mean ± std across folds/episodes.\n"
        "- **Type-3 bounds:** every producer lane bounded by schema-sentinel or submission_validator.\n",
        encoding="utf-8",
    )
    (root / "paper_refs.md").write_text(
        f"# Paper references: {slug}\n\n"
        "- agent-tracing sec/2: agent schemata\n"
        "- sec/3: Chomsky hierarchy mapping\n"
        "- sec/4: evaluation audit protocol\n"
        "- sec/7: R&D Bayesian loop agent\n",
        encoding="utf-8",
    )
    run_sh = root / "run_pipeline.sh"
    run_sh.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
source ~/.bash_profile 2>/dev/null || source ~/.profile 2>/dev/null
mamba activate kc-rogii-wellbore-geology-prediction 2>/dev/null || true
cd /lustre/work/sweeden/frontier-evals/project/paperbench
uv run python -m paperbench.trace_pipeline.orchestrator --variant {slug} --dry-run
uv run python -m paperbench.scripts.implement_agent_tracing --validate-traces
""",
        encoding="utf-8",
    )
    run_sh.chmod(0o755)
    generate_all_phase_notebooks(slug, root / "notebooks", plan)
    print(f"enriched {slug}")


def main() -> None:
    for slug in VARIANTS:
        enrich_variant(slug)


if __name__ == "__main__":
    main()
