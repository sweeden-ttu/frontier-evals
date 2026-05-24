from pathlib import Path

import pytest

from paperbench.chomsky import classify_trace_csv, validate_trace_language_csv
from paperbench.chomsky.producer_consumer import CANONICAL_HEADERS
from paperbench.chomsky.resource_envelope import EXTENDED_HEADERS, ENVELOPE_TOKEN
from paperbench.trace_pipeline.paths import resolve_trace_path


@pytest.fixture
def rogii_baseline() -> Path:
    return resolve_trace_path("baseline_column_transformer")


def test_canonical_header_count() -> None:
    assert len(CANONICAL_HEADERS) == 20
    assert len(EXTENDED_HEADERS) == 29


def test_baseline_has_resource_envelope_block(rogii_baseline: Path) -> None:
    if not rogii_baseline.exists():
        pytest.skip("Rogii traces not present on this host")
    import csv

    with rogii_baseline.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert tuple(rows[0]) == EXTENDED_HEADERS
    assert rows[1][0] == ENVELOPE_TOKEN
    assert rows[1][20] == "Type-0"
    assert any(
        c.strip() == "evaluate_computing_resources_chomsky_rubric" for row in rows for c in row
    )


def test_baseline_trace_validates(rogii_baseline: Path) -> None:
    if not rogii_baseline.exists():
        pytest.skip("Rogii traces not present on this host")
    report = validate_trace_language_csv(rogii_baseline)
    assert report.valid, report.errors


def test_baseline_classified_type0(rogii_baseline: Path) -> None:
    if not rogii_baseline.exists():
        pytest.skip("Rogii traces not present on this host")
    cls = classify_trace_csv(rogii_baseline)
    assert cls.predicted_chomsky_class == "Type-0"
    assert any("CLI" in w or "external" in w.lower() for w in cls.structural_witnesses)
