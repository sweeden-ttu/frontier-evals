import pytest

from paperbench.trace_pipeline.metrics import compute_smre
from paperbench.trace_pipeline.orchestrator import TracePipelineOrchestrator


def test_compute_smre() -> None:
    stats = compute_smre([9.0, 9.5, 8.8])
    assert stats["n"] == 3
    assert 8.8 < stats["mean"] < 9.5


def test_orchestrator_dry_run_baseline() -> None:
    orch = TracePipelineOrchestrator(variant="baseline_column_transformer")
    results = orch.run(dry_run=True)
    assert len(results) > 50
