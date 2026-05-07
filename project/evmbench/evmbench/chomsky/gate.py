"""EVMBench rollout→grading gate.

Realizes the Chomsky V&V producer/consumer relationship for evmbench:

  * **Producer 1** — TraceRecorder over ``runs_dir/<group>/<run>/agent.log``
    using :func:`evmbench_default_alphabet`.
  * **Producer 2** — :func:`scan_veto_log` over ``runs_dir/<group>/<run>/logs/veto.log``.
  * **Consumer**   — :class:`chomsky_vv.ProbeHarness` produces
    ``validation_report_v1`` consumed by the lifecycle gate.

The gate intentionally does not invoke grading; it returns a
:class:`GateResult` and the caller decides whether to proceed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import structlog.stdlib

from chomsky_vv import (
    ChomskyClassification,
    ProbeHarness,
    ProbeVerdict,
    TraceRecorder,
    ValidationReport,
)
from chomsky_vv.schemas import MonitorViolationReport
from evmbench.chomsky.alphabet import evmbench_default_alphabet
from evmbench.chomsky.contracts import classification_for
from evmbench.chomsky.veto_bridge import scan_veto_log

logger = structlog.stdlib.get_logger(component=__name__)


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
    veto_log_file: Path | None = None
    proceed: bool = True
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "mode": self.mode.value,
            "proceed": self.proceed,
            "reason": self.reason,
            "log_file": str(self.log_file) if self.log_file else None,
            "veto_log_file": str(self.veto_log_file) if self.veto_log_file else None,
        }
        if self.validation_report is not None:
            out["validation_report"] = self.validation_report.model_dump(by_alias=True)
        if self.monitor_report is not None:
            out["monitor_report"] = self.monitor_report.model_dump(by_alias=True)
        return out


def _find_logs(run_dir: Path) -> tuple[Path | None, Path | None]:
    """Return (agent_log, veto_log) — both optional."""
    agent_log = next(iter(run_dir.glob("**/agent.log")), None)
    veto_log = next(iter(run_dir.glob("**/veto.log")), None)
    return agent_log, veto_log


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
    agent_id: str = "evm.solver",
    run_id: str | None = None,
    contract: ChomskyClassification | None = None,
    mode: GateMode = GateMode.WARN,
    out_dir: Path | None = None,
) -> GateResult:
    """Run the evmbench detect/patch/exploit gate over a single run dir.

    Args:
        run_dir: ``runs_dir/<group>/<run>`` containing ``agent.log`` and
            (optionally) ``logs/veto.log``.
        agent_id: classification contract to discharge.
        run_id: free-form identifier; defaults to ``run_dir.name``.
        contract: explicit classification; defaults to registry entry.
        mode: ``off`` skips; ``warn`` records but allows; ``block`` refuses.
        out_dir: persist ``chomsky_gate_result.json`` here when set.
    """
    run_dir = Path(run_dir)
    run_id = run_id or run_dir.name
    if mode == GateMode.OFF:
        return GateResult(mode=mode, proceed=True, reason="gate disabled")

    contract = contract or classification_for(agent_id)
    agent_log, veto_log = _find_logs(run_dir)
    if agent_log is None:
        reason = f"no agent.log under {run_dir}"
        logger.warning(reason)
        result = GateResult(mode=mode, proceed=mode != GateMode.BLOCK, reason=reason)
        if out_dir is not None:
            _persist(Path(out_dir), result)
        return result

    alphabet = evmbench_default_alphabet()
    recorder = TraceRecorder(agent_id=agent_id, run_id=run_id, alphabet=alphabet)
    recorder.record_text(
        agent_log.read_text(encoding="utf-8", errors="replace"),
        source_ref=str(agent_log),
    )
    trace = recorder.trace()

    monitor_report: MonitorViolationReport | None = None
    if veto_log is not None:
        monitor_report = scan_veto_log(
            log_path=veto_log, agent_id=agent_id, run_id=run_id
        )

    harness = ProbeHarness(alphabet=alphabet)
    report = harness.run(contract=contract, trace=trace, monitor_report=monitor_report)

    proceed = True
    reason = "gate passed"
    if report.blocked:
        proceed = mode != GateMode.BLOCK
        reason = report.block_reason or "blocked by Veto certifier"
    elif report.overall_verdict == ProbeVerdict.FAIL:
        proceed = mode != GateMode.BLOCK
        reason = (
            f"probe refutation; recommended_class={report.recommended_class.value if report.recommended_class else 'unchanged'}"
        )

    gate_result = GateResult(
        mode=mode,
        validation_report=report,
        monitor_report=monitor_report,
        log_file=agent_log,
        veto_log_file=veto_log,
        proceed=proceed,
        reason=reason,
    )
    if out_dir is not None:
        path = _persist(Path(out_dir), gate_result)
        logger.info(f"chomsky gate result written to {path}")
    return gate_result
