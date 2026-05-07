"""Rollout→grading gate.

Realizes the Chomsky V&V producer/consumer relationship for PaperBench:

  * **Producer 1** — :class:`chomsky_vv.TraceRecorder` discretizes
    ``agent.log`` against :func:`paperbench_default_alphabet` and emits
    ``sigma_trace_v1``.
  * **Producer 2** — :class:`paperbench.monitor.monitor.BasicMonitor`
    scans the same log for blacklist hits; the result is bridged onto
    ``monitor_violation_v1`` via :func:`monitor_result_to_violation_report`.
  * **Consumer** — :class:`chomsky_vv.ProbeHarness` consumes both records
    plus a ``chomsky_classification_v1`` contract, and emits
    ``validation_report_v1``. The gate translates that report into a
    decision:

      * ``GateMode.OFF``    — gate disabled, returns PASS
      * ``GateMode.WARN``   — log violations but allow grading to proceed
      * ``GateMode.BLOCK``  — refuse to grade if the report is blocked or
                              FAIL with a recommended class promotion

The gate intentionally does not invoke grading itself; it returns a
:class:`GateResult` that the caller (``run_judge``) consumes.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
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
from paperbench.chomsky.alphabet import paperbench_default_alphabet
from paperbench.chomsky.contracts import classification_for
from paperbench.chomsky.monitor_bridge import monitor_result_to_violation_report
from paperbench.monitor.monitor import BasicMonitor, Monitor, MonitorResult
from paperbench.paper_registry import paper_registry

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


def find_agent_log(submission_path: Path) -> Path | None:
    """Locate ``agent.log`` inside a paperbench submission tree.

    Mirrors the search used by ``scripts/run_monitor.monitor_single_log``.
    Returns the first match for ``**/logs/agent.log``; falls back to a
    submission tarball under ``submissions/<checkpoint>/`` if the log is
    only available compressed.
    """
    submission_path = Path(submission_path)
    direct = list(submission_path.glob("**/logs/agent.log"))
    if direct:
        return direct[0]
    checkpoints = [
        p
        for p in (submission_path.glob("submissions/*-GMT") or [])
        if p.is_dir()
    ] + [
        p
        for p in (submission_path.glob("submissions/*-UTC") or [])
        if p.is_dir()
    ]
    for checkpoint in sorted(checkpoints, key=lambda x: x.stem, reverse=True):
        tar = checkpoint / "submission.tar.gz"
        if not tar.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(tar, "r:gz") as t:
                t.extractall(path=tmp)
            matches = list(Path(tmp).glob("**/logs/agent.log"))
            if matches:
                staged = checkpoint / "agent.log"
                shutil.copy(matches[0], staged)
                return staged
    return None


async def _run_basic_monitor(
    *, paper_id: str, log_file: Path, monitor_config: Monitor.Config | None = None
) -> MonitorResult:
    paper = paper_registry.get_paper(paper_id)
    monitor = (monitor_config or BasicMonitor.Config()).build(paper=paper)
    return await asyncio.to_thread(monitor.check_log, log_file.as_posix())


def _persist(out_dir: Path, gate_result: GateResult) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = gate_result.to_dict()
    target = out_dir / "chomsky_gate_result.json"
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return target


async def run_rollout_to_grading_gate(
    *,
    submission_path: Path,
    paper_id: str,
    agent_id: str = "pb.basicagent",
    run_id: str | None = None,
    contract: ChomskyClassification | None = None,
    monitor_config: Monitor.Config | None = None,
    mode: GateMode = GateMode.BLOCK,
    out_dir: Path | None = None,
) -> GateResult:
    """Run the rollout→grading gate.

    Args:
        submission_path: directory containing the agent submission (or run
            dir with ``submissions/<checkpoint>/submission.tar.gz``).
        paper_id: paperbench paper identifier (for blacklist resolution).
        agent_id: which Chomsky classification contract to discharge
            obligations against.
        run_id: free-form identifier; defaults to ``submission_path.name``.
        contract: explicit classification contract; defaults to the
            registered default for ``agent_id``.
        monitor_config: alternate Monitor.Config; defaults to BasicMonitor.
        mode: gate behavior (off/warn/block).
        out_dir: if set, persist ``chomsky_gate_result.json`` here.
    """
    submission_path = Path(submission_path)
    run_id = run_id or submission_path.name
    if mode == GateMode.OFF:
        return GateResult(mode=mode, proceed=True, reason="gate disabled")

    contract = contract or classification_for(agent_id)
    log_file = find_agent_log(submission_path)
    if log_file is None:
        reason = f"no agent.log found under {submission_path}"
        logger.warning(reason)
        result = GateResult(
            mode=mode,
            proceed=mode != GateMode.BLOCK,
            reason=reason,
        )
        if out_dir is not None:
            _persist(Path(out_dir), result)
        return result

    monitor_result = await _run_basic_monitor(
        paper_id=paper_id, log_file=log_file, monitor_config=monitor_config
    )
    monitor_report = monitor_result_to_violation_report(
        result=monitor_result, agent_id=agent_id, run_id=run_id
    )

    alphabet = paperbench_default_alphabet()
    recorder = TraceRecorder(agent_id=agent_id, run_id=run_id, alphabet=alphabet)
    recorder.record_text(log_file.read_text(encoding="utf-8", errors="replace"), source_ref=str(log_file))
    trace = recorder.trace()

    harness = ProbeHarness(alphabet=alphabet)
    report = harness.run(
        contract=contract,
        trace=trace,
        monitor_report=monitor_report,
    )

    proceed = True
    reason = "gate passed"
    if report.blocked:
        proceed = mode != GateMode.BLOCK
        reason = report.block_reason or "blocked by non-LLM certifier"
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
        path = _persist(Path(out_dir), gate_result)
        logger.info(f"chomsky gate result written to {path}")
    return gate_result
