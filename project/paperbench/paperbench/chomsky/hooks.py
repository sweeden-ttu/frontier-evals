from __future__ import annotations

import importlib
import json
from pathlib import Path

import structlog

from paperbench.chomsky.classifier import classify_solver_module, classify_trace_csv
from paperbench.chomsky.schema import ChomskyClassificationV1, contracts_dir
from paperbench.chomsky.trace_csv import validate_trace_language_csv
from paperbench.chomsky.verifier import assert_contract_compatible_with_rubric_parser, verify_classification

logger = structlog.stdlib.get_logger(component=__name__)


def run_field_analysis_on_solver(solver_import_path: str) -> ChomskyClassificationV1:
    """Hook: analyze a solver after import. `solver_import_path` is module:attribute."""
    module_path = solver_import_path.split(":")[0]
    mod = importlib.import_module(module_path)
    file_path = Path(mod.__file__) if mod.__file__ else Path(".")
    classification = classify_solver_module(file_path)
    out = contracts_dir() / f"{classification.agent_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(classification.to_json(), encoding="utf-8")
    logger.info("wrote chomsky contract", path=str(out), class_=classification.predicted_chomsky_class)
    return classification


def analyze_trace_and_verify(trace_path: Path) -> dict[str, object]:
    report = validate_trace_language_csv(trace_path)
    classification = classify_trace_csv(trace_path)
    verification = verify_classification(classification, trace_report=report)
    assert_contract_compatible_with_rubric_parser(classification.predicted_chomsky_class)
    contract_path = contracts_dir() / f"{classification.agent_id}.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(classification.to_json(), encoding="utf-8")
    return {
        "trace_path": str(trace_path),
        "validation": report.__dict__,
        "classification": json.loads(classification.to_json()),
        "verification": json.loads(verification.to_json()),
        "contract_path": str(contract_path),
    }
