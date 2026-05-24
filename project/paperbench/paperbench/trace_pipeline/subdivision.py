from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def subdivide_train_by_well(train_df: pd.DataFrame, well_col: str = "well_id") -> list[dict]:
    """Split train into per-well sub-problems."""
    if well_col not in train_df.columns:
        wells = train_df["id"].astype(str).str.split("__").str[0] if "id" in train_df.columns else ["all"]
        train_df = train_df.copy()
        train_df[well_col] = wells
    out: list[dict] = []
    for well, grp in train_df.groupby(well_col):
        out.append({"well": str(well), "n_rows": int(len(grp))})
    return out


def subdivide_train_by_depth_bin(
    train_df: pd.DataFrame,
    depth_col: str = "depth",
    n_bins: int = 5,
) -> list[dict]:
    if depth_col not in train_df.columns:
        return [{"bin": "all", "n_rows": len(train_df)}]
    train_df = train_df.copy()
    train_df["_depth_bin"] = pd.qcut(train_df[depth_col], q=min(n_bins, train_df[depth_col].nunique()), duplicates="drop")
    return [
        {"bin": str(b), "n_rows": int(len(grp))}
        for b, grp in train_df.groupby("_depth_bin", observed=True)
    ]


def write_subdivision_manifest(path: Path | str, *, by_well: list[dict], by_depth: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"by_well": by_well, "by_depth": by_depth}, indent=2),
        encoding="utf-8",
    )
