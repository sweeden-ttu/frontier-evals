"""SWE-Lancer rollout→test-execution gate.

Producer/consumer wiring identical in shape to the paperbench and
evmbench gates, but with the swelancer-specific NEW certifier
(:mod:`swelancer.chomsky.certifier`) replacing the missing third-party
non-LLM certifier slot.

Per the Gap-1 (2b) decision, this gate ships in ``block`` mode with the
certifier in ``ENFORCING`` mode by default — any swelancer rollout that
fails the test-bundle isolation envelope or contains a forbidden import
/ call in a python block is refused. To capture calibration baselines
without filtering, override at the call site: ``mode=GateMode.WARN`` and
``certifier_mode=CertifierMode.ADVISORY``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from chomsky_vv import (
    ChomskyClassification,
    ProbeHarness,
    ProbeVerdict,
    TraceRecorder,
    ValidationReport,
)
from chomsky_vv.schemas import MonitorViolationReport
from swelancer.chomsky.alphabet import swelancer_default_alphabet
from swelancer.chomsky.certifier import CertifierMode, SwelancerCertifier
from swelancer.chomsky.contracts import classification_for


class GateMode(str, Enum):
    OFF = "off"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class GateResult:
    mode: GateMode
    validation_report: ValidationReport | None = None
    monitor_report: MonitorViolationReport | None = None
    log_file: Path | None = None
    proceed: bool = True
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "mode": self.mode.value,
            "proceed": self.proceed,
            "reason": self.reason,
            "log_file": str(self.log_file) if self.log_file else None,
        }
        if self.validation_report is not None:
            out["validation_report"] = self.validation_report.model_dump(by_alias=True)
        if self.monitor_report is not None:
            out["monitor_report"] = self.monitor_report.model_dump(by_alias=True)
        return out


def _find_agent_log(run_dir: Path) -> Path | None:
    return next(iter(run_dir.glob("**/agent.log")), None)


def _persist(out_dir: Path, gate_result: GateResult) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "chomsky_gate_result.json"
    target.write_text(
        json.dumps(gate_result.to_dict(), indent=2, default=str), encoding="utf-8"
    )
    return target


def run_lifecycle_gate(
    *,
    run_dir: Path,
    agent_id: str = "swe.simple_agent",
    run_id: str | None = None,
    contract: ChomskyClassification | None = None,
    mode: GateMode = GateMode.BLOCK,
    certifier_mode: CertifierMode = CertifierMode.ENFORCING,
    out_dir: Path | None = None,
) -> GateResult:
    """Run the swelancer test_execution gate over a single run dir."""
    run_dir = Path(run_dir)
    run_id = run_id or run_dir.name
    if mode == GateMode.OFF:
        return GateResult(mode=mode, proceed=True, reason="gate disabled")

    contract = contract or classification_for(agent_id)
    log_file = _find_agent_log(run_dir)
    if log_file is None:
        result = GateResult(
            mode=mode,
            proceed=mode != GateMode.BLOCK,
            reason=f"no agent.log under {run_dir}",
        )
        if out_dir is not None:
            _persist(Path(out_dir), result)
        return result

    alphabet = swelancer_default_alphabet()
    recorder = TraceRecorder(agent_id=agent_id, run_id=run_id, alphabet=alphabet)
    recorder.record_text(
        log_file.read_text(encoding="utf-8", errors="replace"),
        source_ref=str(log_file),
    )
    trace = recorder.trace()

    certifier = SwelancerCertifier(
        agent_id=agent_id, run_id=run_id, mode=certifier_mode
    )
    monitor_report = certifier.scan_log(log_file)

    harness = ProbeHarness(alphabet=alphabet)
    report = harness.run(contract=contract, trace=trace, monitor_report=monitor_report)

    proceed = True
    reason = "gate passed"
    if report.blocked:
        proceed = mode != GateMode.BLOCK
        reason = report.block_reason or "blocked by swelancer non-LLM certifier"
    elif report.overall_verdict == ProbeVerdict.FAIL:
        proceed = mode != GateMode.BLOCK
        reason = (
            f"probe refutation; recommended_class={report.recommended_class.value if report.recommended_class else 'unchanged'}"
        )

    gate_result = GateResult(
        mode=mode,
        validation_report=report,
        monitor_report=monitor_report,
        log_file=log_file,
        proceed=proceed,
        reason=reason,
    )
    if out_dir is not None:
        _persist(Path(out_dir), gate_result)
    return gate_result
