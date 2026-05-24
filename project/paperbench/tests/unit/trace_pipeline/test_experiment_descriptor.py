"""Tests for experiment_descriptor (paper base + trace CSV join)."""

from __future__ import annotations

import json
from pathlib import Path

from paperbench.trace_pipeline.experiment_descriptor import (
    VARIANT_BASE_PAPERS,
    build_experiment_descriptor,
    load_experiment_descriptor,
    render_paper_refs_md,
    write_experiment_descriptor,
)


def test_all_variants_have_base_paper():
    assert len(VARIANT_BASE_PAPERS) == 6
    for slug, paper in VARIANT_BASE_PAPERS.items():
        assert paper["title"]
        assert paper["claims"]
        assert paper["trace_theory_sections"]


def test_build_descriptor_links_paper_and_trace(tmp_path: Path):
    variant = "baseline_column_transformer"
    desc = build_experiment_descriptor(variant, rogii_root=tmp_path)
    assert desc["base_paper"]["role"] == "model_experiment_descriptor"
    assert len(desc["base_papers"]) == 2
    assert desc["base_papers"][1]["id"] == "pedregosa2011_sklearn"
    assert desc["branch"] == "trace/baseline-column-transformer"
    assert desc["github_pr"] == "17"
    assert desc["agent_implementation"]["trace_language_csv"].endswith(
        "baseline_column_transformer/trace_language.csv"
    )
    assert desc["trace_theory_paper"]["paperbench_id"] == "agent-tracing"
    assert "LightGBM" in desc["base_paper"]["title"]


def test_write_and_load_roundtrip(tmp_path: Path):
    variant = "robust_scale_log1p"
    path = write_experiment_descriptor(variant, out_dir=tmp_path / variant, rogii_root=tmp_path)
    loaded = load_experiment_descriptor(path)
    assert loaded["variant"] == variant
    assert json.loads(path.read_text())["experiment"]["primary_metric"] == "rmse_post_ps"


def test_paper_refs_md_mentions_both_layers(tmp_path: Path):
    variant = "baseline_column_transformer"
    desc = build_experiment_descriptor(variant, rogii_root=tmp_path)
    md = render_paper_refs_md(desc)
    assert "Base papers" in md
    assert "Pedregosa" in md
    assert "LightGBM" in md
    assert "trace_language.csv" in md
    assert "agent-tracing" in md
    assert "PR:" in md
