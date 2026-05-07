"""Bridge: PaperBench :class:`MonitorResult` → ``monitor_violation_v1``.

The PaperBench Monitor and the chomsky_vv harness must share the same
contract type so the harness can fold non-LLM-certifier verdicts into the
``validation_report_v1``. This module performs that translation only — it
does not invoke either side.
"""

from __future__ import annotations

from typing import Literal

from chomsky_vv import MonitorViolation, MonitorViolationReport
from paperbench.monitor.monitor import MonitorResult


def monitor_result_to_violation_report(
    *,
    result: MonitorResult,
    agent_id: str,
    run_id: str,
    monitor_id: str = "paperbench.basic_monitor",
    severity: Literal["info", "warn", "error"] = "error",
) -> MonitorViolationReport:
    violations: list[MonitorViolation] = []
    for v in result.violations:
        excerpt = ""
        if v.context:
            offset = max(0, v.line_number - v.context_start)
            excerpt = v.context[offset] if 0 <= offset < len(v.context) else v.context[0]
        violations.append(
            MonitorViolation(
                rule_id=v.violation,
                severity=severity,
                source_ref=f"{result.log_file}:{v.line_number}",
                excerpt=excerpt[:200],
            )
        )
    return MonitorViolationReport(
        agent_id=agent_id,
        run_id=run_id,
        monitor_id=monitor_id,
        violations=violations,
    )
