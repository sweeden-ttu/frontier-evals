from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupKFold


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
    df = train_df.copy()
    col = depth_col if depth_col in df.columns else None
    if col is None:
        for candidate in ("MD", "md", "depth", "DEPTH"):
            if candidate in df.columns:
                col = candidate
                break
    if col is None:
        return [{"bin": "all", "n_rows": len(df)}]
    uniq = df[col].nunique(dropna=True)
    if uniq < 2:
        return [{"bin": "all", "n_rows": len(df)}]
    df["_depth_bin"] = pd.qcut(df[col], q=min(n_bins, uniq), duplicates="drop")
    return [
        {"bin": str(b), "n_rows": int(len(grp))}
        for b, grp in df.groupby("_depth_bin", observed=True)
    ]


def nested_groupkfold_emit_fold_indices(
    train_df: pd.DataFrame,
    *,
    group_col: str = "well_id",
    n_splits: int = 5,
) -> list[dict]:
    """Emit nested GroupKFold index lists grouped by well."""
    df = train_df.copy()
    if group_col not in df.columns:
        if "id" in df.columns:
            df[group_col] = df["id"].astype(str).str.split("__").str[0]
        else:
            df[group_col] = "all"
    groups = df[group_col].astype(str)
    n_groups = groups.nunique()
    if n_groups < 2:
        return [
            {
                "fold": 0,
                "n_splits": 1,
                "train_indices": list(range(len(df))),
                "test_indices": [],
                "n_train": len(df),
                "n_test": 0,
                "groups": sorted(groups.unique().tolist()),
            }
        ]
    splits = min(n_splits, n_groups)
    gkf = GroupKFold(n_splits=splits)
    folds: list[dict] = []
    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(df, groups=groups)):
        folds.append(
            {
                "fold": fold_idx,
                "n_splits": splits,
                "train_indices": train_idx.tolist(),
                "test_indices": test_idx.tolist(),
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "train_wells": sorted(groups.iloc[train_idx].unique().tolist()),
                "test_wells": sorted(groups.iloc[test_idx].unique().tolist()),
            }
        )
    return folds


def load_rogii_train_frame(data_dir: Path | str) -> pd.DataFrame:
    """Load competition train rows from Rogii data/ (train/ or _train_* snapshots)."""
    data_dir = Path(data_dir)
    paths: list[Path] = []
    train_dir = data_dir / "train"
    if train_dir.is_dir():
        paths.extend(sorted(train_dir.glob("*__horizontal_well.csv")))
    paths.extend(sorted(data_dir.glob("_train_*horizontal_well.csv")))
    paths.extend(sorted(data_dir.glob("_train_*__horizontal_well.csv")))

    seen: set[Path] = set()
    frames: list[pd.DataFrame] = []
    for path in paths:
        path = path.resolve()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        stem = path.stem
        well = stem.replace("__horizontal_well", "").replace("_horizontal_well", "")
        well = well.removeprefix("_train_").removeprefix("_test_")
        chunk = pd.read_csv(path)
        chunk["well_id"] = well
        chunk["source_file"] = path.name
        frames.append(chunk)
    if not frames:
        raise FileNotFoundError(
            f"No train horizontal well CSVs under {data_dir} (expected train/*__horizontal_well.csv or _train_*)"
        )
    return pd.concat(frames, ignore_index=True)


def build_subdivision_manifest(
    *,
    variant: str,
    train_df: pd.DataFrame,
    n_splits: int = 5,
    depth_bins: int = 5,
    data_dir: Path | str | None = None,
) -> dict:
    by_well = subdivide_train_by_well(train_df)
    by_depth = subdivide_train_by_depth_bin(train_df, n_bins=depth_bins)
    folds = nested_groupkfold_emit_fold_indices(train_df, n_splits=n_splits)
    return {
        "variant": variant,
        "data_dir": str(data_dir) if data_dir else None,
        "n_rows": int(len(train_df)),
        "n_wells": len(by_well),
        "by_well": by_well,
        "by_depth": by_depth,
        "nested_groupkfold": folds,
    }


def write_subdivision_manifest(path: Path | str, *, by_well: list[dict], by_depth: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"by_well": by_well, "by_depth": by_depth}, indent=2),
        encoding="utf-8",
    )


def write_full_subdivision_manifest(path: Path | str, manifest: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
