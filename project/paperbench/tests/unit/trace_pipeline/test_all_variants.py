import pytest

from paperbench.chomsky import classify_trace_csv, validate_trace_language_csv
from paperbench.trace_pipeline.orchestrator import TracePipelineOrchestrator
from paperbench.trace_pipeline.paths import resolve_trace_path

VARIANTS = (
    "baseline_column_transformer",
    "typewell_gr_alignment",
    "ps_point_leakage_aware",
    "robust_scale_log1p",
    "parallel_multiwell_loader",
    "formation_plane_spatial",
)


@pytest.mark.parametrize("variant", VARIANTS)
def test_variant_trace_validates(variant: str) -> None:
    path = resolve_trace_path(variant)
    assert path.exists(), path
    report = validate_trace_language_csv(path, require_canonical_header=False)
    assert report.valid, report.errors


@pytest.mark.parametrize("variant", VARIANTS)
def test_variant_classified_type0(variant: str) -> None:
    path = resolve_trace_path(variant)
    cls = classify_trace_csv(path)
    assert cls.predicted_chomsky_class == "Type-0"


@pytest.mark.parametrize("variant", VARIANTS)
def test_orchestrator_dry_run(variant: str) -> None:
    orch = TracePipelineOrchestrator(variant=variant)
    results = orch.run(dry_run=True)
    assert len(results) > 40
