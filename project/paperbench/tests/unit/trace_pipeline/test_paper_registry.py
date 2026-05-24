"""Tests for Rogii paper PDF registry."""

from __future__ import annotations

from pathlib import Path

from paperbench.trace_pipeline.paper_registry import (
    list_all_pdfs,
    resolve_papers_root,
    resolve_variant_pdf,
)


def test_resolve_papers_root_exists():
    root = resolve_papers_root()
    assert root is not None
    assert root.is_dir()


def test_baseline_primary_pdf():
    pdf = resolve_variant_pdf("baseline_column_transformer")
    assert pdf is not None
    assert pdf.name == "ke2017_lightgbm.pdf"
    assert pdf.stat().st_size > 5000


def test_typewell_primary_pdf():
    pdf = resolve_variant_pdf("typewell_gr_alignment")
    assert pdf is not None
    assert "sakoe" in pdf.name


def test_list_all_pdfs_non_empty():
    pdfs = list_all_pdfs()
    assert len(pdfs) >= 6
    assert all(p.suffix == ".pdf" for p in pdfs)
