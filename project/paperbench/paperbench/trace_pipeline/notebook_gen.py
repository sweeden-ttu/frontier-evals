from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PHASES = (
    "01_data_analysis",
    "02_statistical_framework",
    "03_feature_engineering",
    "04_model_training",
    "05_evaluation",
    "06_submission",
)


def generate_phase_notebook(
    *,
    phase: str,
    variant: str,
    out_dir: Path | str,
    mle_plan: dict | None = None,
) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nb_path = out_dir / f"{phase}.ipynb"
    plan_snippet = json.dumps(mle_plan or {}, indent=2)[:2000]
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# {phase.replace('_', ' ').title()}\n",
                f"Variant: `{variant}`\n",
            ],
        },
        {
            "cell_type": "code",
            "metadata": {},
            "source": [
                f'VARIANT = "{variant}"\n',
                f'PHASE = "{phase}"\n',
                f"MLE_PLAN = {json.dumps(mle_plan or {})}\n",
            ],
            "outputs": [],
            "execution_count": None,
        },
    ]
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": cells,
    }
    nb_path.write_text(json.dumps(nb, indent=2), encoding="utf-8")
    return nb_path


def generate_all_phase_notebooks(variant: str, out_dir: Path | str, mle_plan: dict | None = None) -> list[Path]:
    return [generate_phase_notebook(phase=p, variant=variant, out_dir=out_dir, mle_plan=mle_plan) for p in NOTEBOOK_PHASES]
