"""Resolve Rogii variant / layer PDFs from agent-tracing worktrees."""

from __future__ import annotations

import json
import os
from pathlib import Path

_PAPERBENCH_ROOT = Path(__file__).resolve().parents[2]

# Search order: explicit env, trace-baseline (canonical), agent-tracing, bundled data.
_CANDIDATE_PAPER_ROOTS: tuple[Path, ...] = (
    Path("/lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii/papers"),
    Path("/lustre/work/sweeden/agent-tracing/examples/rogii/papers"),
    _PAPERBENCH_ROOT / "data" / "rogii" / "papers",
)

_VARIANT_PRIMARY_PDF: dict[str, str] = {
    "baseline_column_transformer": "baseline_column_transformer/ke2017_lightgbm.pdf",
    "typewell_gr_alignment": "typewell_gr_alignment/sakoe1978_dtw.pdf",
    "ps_point_leakage_aware": "ps_point_leakage_aware/kaufman2012_leakage.pdf",
    "robust_scale_log1p": "robust_scale_log1p/pedregosa2011_sklearn_robust_substitute.pdf",
    "parallel_multiwell_loader": "parallel_multiwell_loader/rocklin2015_dask.pdf",
    "formation_plane_spatial": "formation_plane_spatial/cover1967_knn.pdf",
}

_VARIANT_SUPPORTING_PDF: dict[str, list[str]] = {
    "baseline_column_transformer": ["baseline_column_transformer/pedregosa2011_sklearn.pdf"],
    "formation_plane_spatial": ["formation_plane_spatial/shepard1968_interpolation.pdf"],
}


def resolve_papers_root() -> Path | None:
    if env := os.environ.get("ROGII_PAPERS_ROOT"):
        p = Path(env)
        return p if p.is_dir() else None
    for root in _CANDIDATE_PAPER_ROOTS:
        if root.is_dir():
            return root
    return None


def _valid_pdf(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 5000 and path.read_bytes()[:5].startswith(b"%PDF")


def resolve_variant_pdf(variant: str, *, primary: bool = True) -> Path | None:
    root = resolve_papers_root()
    if root is None:
        return None
    rel = _VARIANT_PRIMARY_PDF.get(variant)
    if not rel:
        return None
    candidate = root / rel
    return candidate if _valid_pdf(candidate) else None


def resolve_variant_paper_set(variant: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    primary = resolve_variant_pdf(variant)
    if primary:
        out["primary"] = primary
    root = resolve_papers_root()
    if root:
        for rel in _VARIANT_SUPPORTING_PDF.get(variant, []):
            p = root / rel
            if _valid_pdf(p):
                out[Path(rel).stem] = p
    return out


def paper_file_for_descriptor(variant: str, variant_dir: Path) -> str | None:
    """Relative path from ``variant_dir`` to primary PDF for experiment_descriptor.json."""
    pdf = resolve_variant_pdf(variant)
    if pdf is None:
        return None
    try:
        return os.path.relpath(pdf, variant_dir)
    except ValueError:
        return str(pdf)


def load_manifest(root: Path | None = None) -> dict:
    root = root or resolve_papers_root()
    if root is None:
        return {"papers": []}
    manifest = root / "manifest.json"
    if manifest.is_file():
        return json.loads(manifest.read_text(encoding="utf-8"))
    return {"papers": []}


def list_all_pdfs() -> list[Path]:
    root = resolve_papers_root()
    if root is None:
        return []
    return sorted(p for p in root.rglob("*.pdf") if _valid_pdf(p))
