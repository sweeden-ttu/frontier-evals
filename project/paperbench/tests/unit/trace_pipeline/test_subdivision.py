import pandas as pd
import pytest

from paperbench.trace_pipeline.subdivision import (
    build_subdivision_manifest,
    nested_groupkfold_emit_fold_indices,
    subdivide_train_by_depth_bin,
    subdivide_train_by_well,
)


@pytest.fixture
def sample_train() -> pd.DataFrame:
    rows = []
    for well in ("000d7d20", "00bbac68", "00e12e8b"):
        for md in range(100, 120):
            rows.append({"well_id": well, "MD": float(md), "TVT": md * 0.1})
    return pd.DataFrame(rows)


def test_subdivide_by_well(sample_train: pd.DataFrame) -> None:
    wells = subdivide_train_by_well(sample_train)
    assert len(wells) == 3
    assert sum(w["n_rows"] for w in wells) == len(sample_train)


def test_subdivide_by_depth_uses_md(sample_train: pd.DataFrame) -> None:
    bins = subdivide_train_by_depth_bin(sample_train, depth_col="MD", n_bins=3)
    assert len(bins) >= 2


def test_nested_groupkfold(sample_train: pd.DataFrame) -> None:
    folds = nested_groupkfold_emit_fold_indices(sample_train, n_splits=3)
    assert len(folds) == 3
    assert folds[0]["n_test"] > 0


def test_build_manifest(sample_train: pd.DataFrame) -> None:
    manifest = build_subdivision_manifest(variant="baseline_column_transformer", train_df=sample_train)
    assert manifest["variant"] == "baseline_column_transformer"
    assert manifest["n_wells"] == 3
    assert "nested_groupkfold" in manifest
    assert len(manifest["by_depth"]) >= 1
