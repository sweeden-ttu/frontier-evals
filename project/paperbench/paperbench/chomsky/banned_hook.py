"""PaperBench judge post-hook for the chomsky_vv banned-token punisher.

Runs :class:`chomsky_vv.BannedTokenCertifier` against the submission tree
and (optionally) the judge transcript, then routes the resulting
:class:`MonitorViolationReport` through the existing
:class:`MonitorCertifierProbe` so the consumer's
``validation_report_v1`` records ``blocked=True`` on any error-severity
hit. This module deliberately does not invoke the judge itself; callers
embed the post-hook into the judge pipeline by importing
:func:`run_banned_token_judge_post_hook`.

The hook is composable with the existing
:func:`run_rollout_to_grading_gate`: the banned-token report can be
merged into the PaperBench Monitor report via
:func:`merge_monitor_reports` before the gate runs, so a single
``validation_report_v1`` carries both signals.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import structlog.stdlib

from chomsky_vv import (
    Alphabet,
    BannedTokenCertifier,
    BannedTokenPolicy,
    ChomskyClass,
    ChomskyClassification,
    MemoryHypothesis,
    MonitorViolationReport,
    ProbeResult,
    ProbeVerdict,
    TraceRecord,
    ValidationReport,
    VVObligationBudget,
    default_policy,
)
from chomsky_vv.alphabet import TokenSpec
from chomsky_vv.banned import compute_penalty
from chomsky_vv.probes.monitor_certifier import MonitorCertifierProbe

logger = structlog.stdlib.get_logger(component=__name__)


@dataclass
class BannedTokenJudgeResult:
    """Output of :func:`run_banned_token_judge_post_hook`."""

    monitor_report: MonitorViolationReport
    probe_result: ProbeResult
    validation_report: ValidationReport
    penalty: float
    blocked: bool
    paths_scanned: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "monitor_report": self.monitor_report.model_dump(by_alias=True),
            "probe_result": self.probe_result.model_dump(),
            "validation_report": self.validation_report.model_dump(by_alias=True),
            "penalty": self.penalty,
            "blocked": self.blocked,
            "paths_scanned": list(self.paths_scanned),
        }


def merge_monitor_reports(
    *reports: MonitorViolationReport,
    monitor_id: str = "paperbench.banned+monitor",
) -> MonitorViolationReport:
    """Combine multiple ``MonitorViolationReport``s into one.

    Useful for fusing a PaperBench Monitor verdict with a banned-token
    verdict before passing the merged report into the gate.
    """
    if not reports:
        raise ValueError("merge_monitor_reports requires at least one report")
    head = reports[0]
    violations = []
    for r in reports:
        violations.extend(r.violations)
    return MonitorViolationReport(
        agent_id=head.agent_id,
        run_id=head.run_id,
        monitor_id=monitor_id,
        violations=violations,
    )


def _stub_alphabet() -> Alphabet:
    """A minimal alphabet used when the hook runs probe-only.

    The BannedToken probe never inspects the trace, so any non-empty
    alphabet is sufficient to satisfy the probe contract.
    """
    return Alphabet(tokens=[TokenSpec(name="bash", pattern=r"BASH")])


def _stub_contract(agent_id: str) -> ChomskyClassification:
    return ChomskyClassification(
        agent_id=agent_id,
        source_paths=["<banned-hook>"],
        sigma_trace_alphabet_encoding=["bash"],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        memory_hypothesis=MemoryHypothesis(
            workspace_class="bounded", external_store="none"
        ),
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=8,
            test_case_count=4,
            judge_call_budget=2,
        ),
    )


def _empty_trace(agent_id: str, run_id: str) -> TraceRecord:
    return TraceRecord(agent_id=agent_id, run_id=run_id, tokens=[])


def _validation_report_from_probe(
    *,
    agent_id: str,
    run_id: str,
    contract: ChomskyClassification,
    probe: ProbeResult,
    monitor_report: MonitorViolationReport,
) -> ValidationReport:
    """Build a ``validation_report_v1`` from a single probe result."""
    blocked = monitor_report.has_blocking_violation or probe.verdict is ProbeVerdict.FAIL
    block_reason = (
        f"banned-token certifier reported {len(monitor_report.violations)} "
        f"violation(s) including {sum(1 for v in monitor_report.violations if v.severity == 'error')} "
        "error-severity hit(s)"
        if blocked
        else None
    )
    overall: ProbeVerdict
    if blocked:
        overall = ProbeVerdict.FAIL
    elif probe.verdict is ProbeVerdict.PASS:
        overall = ProbeVerdict.PASS
    else:
        overall = probe.verdict
    return ValidationReport(
        agent_id=agent_id,
        run_id=run_id,
        declared_class=contract.predicted_chomsky_class,
        probe_results=[probe],
        recommended_class=probe.refutes_class if blocked else None,
        overall_verdict=overall,
        blocked=blocked,
        block_reason=block_reason,
    )


def run_banned_token_judge_post_hook(
    *,
    submission_path: Path | str,
    judge_transcript_path: Path | str | None = None,
    extra_paths: Iterable[Path | str] = (),
    agent_id: str = "pb.basicagent",
    run_id: str | None = None,
    contract: ChomskyClassification | None = None,
    policy: BannedTokenPolicy | None = None,
    out_dir: Path | str | None = None,
) -> BannedTokenJudgeResult:
    """Run the banned-token certifier and emit a ``validation_report_v1``.

    Args:
        submission_path: directory containing the agent submission tree.
        judge_transcript_path: optional path to the judge's transcript
            file or directory; included in the scan so violations in
            judge prompts/outputs are also caught.
        extra_paths: additional paths to scan (e.g. agent logs).
        agent_id: agent identifier carried into ``validation_report_v1``.
        run_id: free-form run identifier; defaults to
            ``submission_path.name``.
        contract: explicit classification contract; defaults to a stub
            Type-3 contract that satisfies the probe interface.
        policy: explicit ``BannedTokenPolicy``; defaults to the bundled
            policy.
        out_dir: if set, persist
            ``banned_token_judge_post_hook.json`` under this directory.
    """
    submission_path = Path(submission_path)
    run_id = run_id or submission_path.name
    pol = policy or default_policy()
    contract = contract or _stub_contract(agent_id)

    targets: list[Path] = [submission_path]
    if judge_transcript_path is not None:
        targets.append(Path(judge_transcript_path))
    for extra in extra_paths:
        targets.append(Path(extra))

    certifier = BannedTokenCertifier(
        monitor_id="paperbench.banned",
        agent_id=agent_id,
        run_id=run_id,
        policy=pol,
    )
    monitor_report = certifier.scan(targets)

    probe = MonitorCertifierProbe()
    probe_result = probe.run(
        contract=contract,
        trace=_empty_trace(agent_id, run_id),
        alphabet=_stub_alphabet(),
        monitor_report=monitor_report,
    )
    validation_report = _validation_report_from_probe(
        agent_id=agent_id,
        run_id=run_id,
        contract=contract,
        probe=probe_result,
        monitor_report=monitor_report,
    )
    penalty = compute_penalty(monitor_report, pol)
    result = BannedTokenJudgeResult(
        monitor_report=monitor_report,
        probe_result=probe_result,
        validation_report=validation_report,
        penalty=penalty,
        blocked=validation_report.blocked,
        paths_scanned=[str(p) for p in targets],
    )
    if out_dir is not None:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        target = out_path / "banned_token_judge_post_hook.json"
        target.write_text(json.dumps(result.to_dict(), indent=2, default=str), encoding="utf-8")
        logger.info(f"banned-token judge post-hook result written to {target}")
    return result


__all__ = [
    "BannedTokenJudgeResult",
    "merge_monitor_reports",
    "run_banned_token_judge_post_hook",
]
