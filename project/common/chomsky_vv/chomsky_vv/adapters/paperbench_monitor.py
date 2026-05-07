"""PaperBench Monitor adapter.

Wraps the existing ``paperbench.monitor.Monitor`` (a Type-3 non-LLM
certifier) so its output can flow on the Chomsky V&V contract bus as a
``monitor_violation_v1`` record.

The adapter is import-light by design: we do not import paperbench here.
The caller passes either:

  * a list of ``(rule_id, line_no, line_text)`` tuples from a custom run, or
  * a path to ``agent.log`` plus a sequence of (rule_id, regex) patterns,
    which we scan ourselves with stdlib ``re`` so the adapter stays
    pure-Python and Type-2-bounded.

If the live ``paperbench.monitor.Monitor`` is invoked elsewhere, its
``MonitorResult``/``Violation`` rows can be mapped via
``monitor_blacklist_to_violations``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from chomsky_vv.schemas import MonitorViolation, MonitorViolationReport


@dataclass
class _RulePattern:
    rule_id: str
    pattern: re.Pattern[str]
    severity: Literal["info", "warn", "error"] = "error"


def _compile_rules(rules: Iterable[tuple[str, str]]) -> list[_RulePattern]:
    return [_RulePattern(rule_id=rid, pattern=re.compile(pat)) for rid, pat in rules]


@dataclass
class PaperBenchMonitorAdapter:
    monitor_id: str
    agent_id: str
    run_id: str
    rules: list[tuple[str, str]]

    def scan_log(self, log_path: Path | str) -> MonitorViolationReport:
        compiled = _compile_rules(self.rules)
        violations: list[MonitorViolation] = []
        path = Path(log_path)
        if not path.exists():
            return MonitorViolationReport(
                agent_id=self.agent_id,
                run_id=self.run_id,
                monitor_id=self.monitor_id,
            )
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for lineno, raw in enumerate(fh, start=1):
                line = raw.rstrip("\n")
                for rp in compiled:
                    if rp.pattern.search(line):
                        violations.append(
                            MonitorViolation(
                                rule_id=rp.rule_id,
                                severity=rp.severity,
                                source_ref=f"{path}:{lineno}",
                                excerpt=line[:200],
                            )
                        )
        return MonitorViolationReport(
            agent_id=self.agent_id,
            run_id=self.run_id,
            monitor_id=self.monitor_id,
            violations=violations,
        )


def monitor_blacklist_to_violations(
    *,
    monitor_id: str,
    agent_id: str,
    run_id: str,
    hits: Iterable[tuple[str, str, str]],
    severity: Literal["info", "warn", "error"] = "error",
) -> MonitorViolationReport:
    """Convert ``(rule_id, source_ref, excerpt)`` triples into a report.

    Use when the live PaperBench Monitor produces structured hits and you
    just need to wrap them on the contract bus."""
    return MonitorViolationReport(
        agent_id=agent_id,
        run_id=run_id,
        monitor_id=monitor_id,
        violations=[
            MonitorViolation(
                rule_id=rid,
                severity=severity,
                source_ref=src,
                excerpt=excerpt[:200],
            )
            for rid, src, excerpt in hits
        ],
    )
