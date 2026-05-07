"""Probe harness — consumer of ``sigma_trace_v1`` + ``monitor_violation_v1``.

The harness is the single consumer entry-point on the Chomsky V&V contract
bus. It runs the configured probes against a ``ChomskyClassification``
contract and a ``TraceRecord``, optionally folding in a Monitor verdict
and a multi-trace P4 fit, and returns a ``validation_report_v1``.

Aggregation rule: any FAIL with a non-null ``refutes_class`` strictly
promotes the recommended class toward Type-0 (most permissive). The
overall verdict is FAIL if any probe failed; ``blocked`` is set when a
non-LLM certifier (the MonitorCertifierProbe) refuted, since that signals
a safety predicate violation independent of class.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from chomsky_vv.alphabet import Alphabet
from chomsky_vv.probes import (
    MonitorCertifierProbe,
    P1Pumping,
    P2BalancedDepth,
    P3CrossSerial,
    P4WorkspaceLinearity,
    P5RetrievalSwap,
    P6CopyLanguage,
)
from chomsky_vv.schemas import (
    ChomskyClass,
    ChomskyClassification,
    MonitorViolationReport,
    ProbeResult,
    ProbeVerdict,
    TraceRecord,
    ValidationReport,
    class_rank,
    promote,
)


@dataclass
class ProbeHarness:
    alphabet: Alphabet
    p1: P1Pumping = field(default_factory=P1Pumping)
    p2: P2BalancedDepth = field(default_factory=P2BalancedDepth)
    p3: P3CrossSerial = field(default_factory=P3CrossSerial)
    p4: P4WorkspaceLinearity = field(default_factory=P4WorkspaceLinearity)
    p5: P5RetrievalSwap = field(default_factory=P5RetrievalSwap)
    p6: P6CopyLanguage = field(default_factory=P6CopyLanguage)
    monitor: MonitorCertifierProbe = field(default_factory=MonitorCertifierProbe)

    def run(
        self,
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        length_traces: Sequence[TraceRecord] | None = None,
        length_inputs: Sequence[int] | None = None,
        baseline_trace: TraceRecord | None = None,
        monitor_report: MonitorViolationReport | None = None,
    ) -> ValidationReport:
        results: list[ProbeResult] = []
        results.append(self.p1.run(contract=contract, trace=trace, alphabet=self.alphabet))
        results.append(self.p2.run(contract=contract, trace=trace, alphabet=self.alphabet))
        results.append(self.p3.run(contract=contract, trace=trace, alphabet=self.alphabet))
        results.append(
            self.p4.run(
                contract=contract,
                traces=length_traces or [trace],
                input_lengths=length_inputs or [len(trace.tokens)],
            )
        )
        results.append(
            self.p5.run(
                contract=contract,
                trace=trace,
                alphabet=self.alphabet,
                baseline_trace=baseline_trace,
            )
        )
        results.append(self.p6.run(contract=contract, trace=trace, alphabet=self.alphabet))
        results.append(
            self.monitor.run(
                contract=contract,
                trace=trace,
                alphabet=self.alphabet,
                monitor_report=monitor_report,
            )
        )
        return self._aggregate(contract=contract, trace=trace, results=results)

    @staticmethod
    def _aggregate(
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        results: list[ProbeResult],
    ) -> ValidationReport:
        failures = [r for r in results if r.verdict == ProbeVerdict.FAIL]
        recommended = contract.predicted_chomsky_class
        for r in failures:
            if r.refutes_class is None:
                continue
            candidate = promote(r.refutes_class)
            if class_rank(candidate) > class_rank(recommended):
                recommended = candidate
        blocked = any(r.probe_id == MonitorCertifierProbe.probe_id and r.verdict == ProbeVerdict.FAIL for r in results)
        block_reason: str | None = None
        if blocked:
            block_reason = "non-LLM certifier (MonitorCertifierProbe) refuted; safety predicate violated"
        overall = ProbeVerdict.FAIL if failures else ProbeVerdict.PASS
        return ValidationReport(
            agent_id=contract.agent_id,
            run_id=trace.run_id,
            declared_class=contract.predicted_chomsky_class,
            probe_results=results,
            overall_verdict=overall,
            recommended_class=recommended if recommended != contract.predicted_chomsky_class else None,
            blocked=blocked,
            block_reason=block_reason,
        )
