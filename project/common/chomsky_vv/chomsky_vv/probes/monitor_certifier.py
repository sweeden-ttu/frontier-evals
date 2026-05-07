"""Non-LLM-certifier probe.

Consumes a ``MonitorViolationReport`` (e.g. from the PaperBench Monitor
adapter) and emits a hard refutation if the certifier reports any
``error``-severity violation. This is the bridge that makes the Monitor
agent a first-class consumer on the Chomsky V&V contract bus, regardless
of the agent's declared Chomsky class.
"""

from __future__ import annotations

from chomsky_vv.alphabet import Alphabet
from chomsky_vv.probes.base import Probe
from chomsky_vv.schemas import (
    ChomskyClass,
    ChomskyClassification,
    MonitorViolationReport,
    ProbeResult,
    ProbeVerdict,
    TraceRecord,
)


class MonitorCertifierProbe(Probe):
    probe_id = "MonitorCertifier"
    targets = frozenset({ChomskyClass.TYPE_0, ChomskyClass.TYPE_1, ChomskyClass.TYPE_2, ChomskyClass.TYPE_3})

    def __init__(self, *, blocks: bool = True) -> None:
        self.blocks = blocks

    def run(
        self,
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        alphabet: Alphabet,
        monitor_report: MonitorViolationReport | None = None,
    ) -> ProbeResult:
        if monitor_report is None:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.SKIPPED,
                notes="no monitor_violation_v1 report supplied",
            )
        errors = [v for v in monitor_report.violations if v.severity == "error"]
        warns = [v for v in monitor_report.violations if v.severity == "warn"]
        evidence: dict[str, object] = {
            "monitor_id": monitor_report.monitor_id,
            "n_errors": len(errors),
            "n_warns": len(warns),
            "rules": sorted({v.rule_id for v in monitor_report.violations}),
        }
        if errors:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.FAIL,
                refutes_class=contract.predicted_chomsky_class,
                evidence=evidence,
                notes="non-LLM certifier reported error-severity violation(s)",
            )
        if warns:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.INCONCLUSIVE,
                evidence=evidence,
                notes="non-LLM certifier reported warn-severity violation(s); not blocking",
            )
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence=evidence,
        )
