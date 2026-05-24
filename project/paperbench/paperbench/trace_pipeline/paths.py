from __future__ import annotations

import os
from pathlib import Path

_PAPERBENCH_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_HPCC_ROGII = Path("/lustre/work/sweeden/rogii")
_BUNDLED_ROGII = _PAPERBENCH_ROOT / "data" / "rogii"
_AGENT_TRACING_EXAMPLES = Path("/lustre/work/sweeden/agent-tracing/examples/rogii")
_AGENT_TRACING_TRACE_BASELINE = Path("/lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii")


def resolve_rogii_root() -> Path:
    """Rogii repo root (contains traces/preprocessing/{variant}/)."""
    if env := os.environ.get("ROGII_ROOT"):
        return Path(env)
    for candidate in (
        _AGENT_TRACING_TRACE_BASELINE,
        _AGENT_TRACING_EXAMPLES,
        _BUNDLED_ROGII,
        _DEFAULT_HPCC_ROGII,
    ):
        if (candidate / "traces" / "preprocessing").is_dir():
            return candidate
    return _DEFAULT_HPCC_ROGII


_DEFAULT_VARIANTS = (
    "baseline_column_transformer",
    "typewell_gr_alignment",
    "ps_point_leakage_aware",
    "robust_scale_log1p",
    "parallel_multiwell_loader",
    "formation_plane_spatial",
)


def discover_variants() -> tuple[str, ...]:
    """Variants present under traces/preprocessing/, else bundled defaults."""
    root = resolve_rogii_root() / "traces" / "preprocessing"
    if root.is_dir():
        found = sorted(
            p.name for p in root.iterdir() if (p / "trace_language.csv").is_file()
        )
        if found:
            return tuple(found)
    return _DEFAULT_VARIANTS


def resolve_trace_path(variant: str) -> Path:
    return (
        resolve_rogii_root()
        / "traces"
        / "preprocessing"
        / variant
        / "trace_language.csv"
    )
