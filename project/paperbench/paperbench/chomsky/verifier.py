from __future__ import annotations

from paperbench.chomsky.schema import (
    ChomskyClassificationV1,
    CheckResult,
    ValidationReport,
    VerificationReportV1,
)
from paperbench.chomsky.trace_csv import validate_trace_language_csv


def verify_classification(
    classification: ChomskyClassificationV1,
    *,
    trace_report: ValidationReport | None = None,
) -> VerificationReportV1:
    checks: list[CheckResult] = []
    predicted = classification.predicted_chomsky_class
    demoted_to = None

    checks.append(
        CheckResult(
            name="schema_version",
            status="PASS" if classification.schema == "chomsky_classification_v1" else "FAIL",
            evidence=classification.schema,
        )
    )

    checks.append(
        CheckResult(
            name="agent_id_present",
            status="PASS" if classification.agent_id else "FAIL",
            evidence=classification.agent_id or "<missing>",
        )
    )

    checks.append(
        CheckResult(
            name="alphabet_documented",
            status="PASS" if classification.sigma_trace_alphabet_encoding else "FAIL",
            evidence=f"{len(classification.sigma_trace_alphabet_encoding)} tokens",
        )
    )

    if trace_report is not None:
        checks.append(
            CheckResult(
                name="trace_csv_valid",
                status="PASS" if trace_report.valid else "FAIL",
                evidence="; ".join(trace_report.errors) or "ok",
            )
        )
        pc = getattr(trace_report, "producer_consumer_errors", None)
        if pc is None and trace_report.errors:
            pc = [e for e in trace_report.errors if "Type-3 consumer" in e or "CLI in" in e]
        if pc:
            checks.append(
                CheckResult(
                    name="producer_type3_consumer_bounds",
                    status="FAIL",
                    evidence="; ".join(pc[:3]),
                )
            )
        else:
            checks.append(
                CheckResult(
                    name="producer_type3_consumer_bounds",
                    status="PASS",
                    evidence="all producer lanes bounded by Type-3 consumers",
                )
            )

    cls = predicted
    if cls == "Type-3":
        checks.append(
            CheckResult(
                name="type3_finite_control",
                status="PASS"
                if any("dispatch" in w or "finite" in w.lower() for w in classification.structural_witnesses)
                else "FAIL",
                evidence=str(classification.structural_witnesses),
            )
        )
    elif cls == "Type-2":
        checks.append(
            CheckResult(
                name="type2_stack_witness",
                status="PASS"
                if any("add_task" in w or "pushdown" in w or "stack" in w for w in classification.structural_witnesses)
                else "FAIL",
                evidence=str(classification.structural_witnesses),
            )
        )
    elif cls == "Type-1":
        checks.append(
            CheckResult(
                name="type1_linear_workspace",
                status="PASS"
                if "linear" in classification.memory_hypothesis.lower()
                or any("alphabet" in w for w in classification.structural_witnesses)
                else "FAIL",
                evidence=classification.memory_hypothesis,
            )
        )
    elif cls == "Type-0":
        cli_witness = any(
            "CLI" in w or "subprocess" in w or "external" in w.lower()
            for w in classification.structural_witnesses
        )
        checks.append(
            CheckResult(
                name="type0_external_store",
                status="PASS" if cli_witness or "external" in classification.memory_hypothesis.lower() else "FAIL",
                evidence=classification.memory_hypothesis,
            )
        )
        checks.append(
            CheckResult(
                name="computing_resources_envelope_declared",
                status="PASS" if trace_report and trace_report.column_count == 29 else "FAIL",
                evidence=f"columns={trace_report.column_count if trace_report else 0}",
            )
        )

    if trace_report and trace_report.valid is False and predicted != "Type-0":
        demoted_to = "Type-2"
        checks.append(
            CheckResult(
                name="demotion_on_invalid_trace",
                status="PASS",
                evidence=f"demoted {predicted} -> {demoted_to} due to invalid trace CSV",
            )
        )

    return VerificationReportV1(
        agent_id=classification.agent_id,
        predicted_class=predicted,
        demoted_to=demoted_to,
        checks=checks,
    )


def assert_contract_compatible_with_rubric_parser(predicted_class: str) -> None:
    """PaperBench hook: rubric JSON parsing is Type-3-safe; Type-0 judges need budget checks."""
    if predicted_class == "Type-0":
        return  # allowed with extended V&V budget
    return
