from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def compute_smre(fold_rmses: list[float]) -> dict[str, float]:
    """SMRE: mean RMSE ± std across folds/episodes."""
    if not fold_rmses:
        return {"mean": float("nan"), "std": float("nan"), "n": 0}
    arr = np.asarray(fold_rmses, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "n": int(len(arr)),
    }


def write_smre_report(path: Path | str, fold_rmses: list[float]) -> dict[str, float]:
    stats = compute_smre(fold_rmses)
    payload = {"smre": stats, "fold_rmses": fold_rmses}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return stats
