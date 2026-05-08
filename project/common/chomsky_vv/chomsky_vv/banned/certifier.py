"""Non-LLM certifier that emits a ``MonitorViolationReport``.

The certifier is a thin adapter: it scans a path tree (or a raw text
blob) with :class:`BannedTokenMatcher` and converts each ``Hit`` into a
:class:`chomsky_vv.schemas.MonitorViolation`. The resulting report flows
straight into the existing :class:`MonitorCertifierProbe`, so we do not
introduce a new probe class — keeping the contract bus minimal.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from chomsky_vv.banned.matcher import BannedTokenMatcher, Hit
from chomsky_vv.banned.policy import BannedTokenPolicy, default_policy
from chomsky_vv.schemas import MonitorViolation, MonitorViolationReport


@dataclass
class BannedTokenCertifier:
    """Adapter from a path tree to a ``MonitorViolationReport``."""

    monitor_id: str = "BannedTokenCertifier"
    agent_id: str = "unknown"
    run_id: str = "unknown"
    policy: BannedTokenPolicy = field(default_factory=default_policy)

    def __post_init__(self) -> None:
        self._matcher = BannedTokenMatcher(self.policy)

    @property
    def matcher(self) -> BannedTokenMatcher:
        return self._matcher

    def scan(
        self, paths: str | Path | Iterable[str | Path]
    ) -> MonitorViolationReport:
        """Scan one path or an iterable of paths and emit a report."""
        if isinstance(paths, (str, Path)):
            target_paths: list[str | Path] = [paths]
        else:
            target_paths = list(paths)
        all_hits: list[Hit] = []
        for p in target_paths:
            all_hits.extend(self._matcher.scan_path(p))
        return self._to_report(all_hits)

    def scan_text(self, source: str, ref: str = "<text>") -> MonitorViolationReport:
        """Scan an in-memory text blob (e.g. an LLM completion)."""
        return self._to_report(self._matcher.scan_text(source, ref))

    def scan_python(self, source: str, ref: str = "<python>") -> MonitorViolationReport:
        """Scan an in-memory Python source string."""
        return self._to_report(self._matcher.scan_python(source, ref))

    def _to_report(self, hits: list[Hit]) -> MonitorViolationReport:
        violations = [
            MonitorViolation(
                rule_id=f"banned:{h.token}",
                severity=h.severity,  # type: ignore[arg-type]
                source_ref=f"{h.file}:{h.line}:{h.col}",
                excerpt=h.excerpt[:200],
            )
            for h in hits
        ]
        return MonitorViolationReport(
            agent_id=self.agent_id,
            run_id=self.run_id,
            monitor_id=self.monitor_id,
            violations=violations,
        )
