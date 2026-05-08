"""Numeric penalty arithmetic shared by every enforcement layer.

The grader hook, the RL reward shaper, and the probe-side aggregator
all read severity factors and per-token weights from one place so that
tweaking ``policy.yaml`` is the single lever for punishment intensity.
"""

from __future__ import annotations

from chomsky_vv.banned.policy import BannedTokenPolicy
from chomsky_vv.schemas import MonitorViolationReport

SEVERITY_FACTOR: dict[str, float] = {"info": 0.1, "warn": 0.4, "error": 1.0}


def _token_from_rule_id(rule_id: str) -> str:
    if rule_id.startswith("banned:"):
        return rule_id[len("banned:") :]
    return rule_id


def compute_penalty(report: MonitorViolationReport, policy: BannedTokenPolicy) -> float:
    """Return ``sum(weight[token] * severity_factor)`` over the report."""
    total = 0.0
    for v in report.violations:
        token = _token_from_rule_id(v.rule_id)
        weight = policy.weight_for(token)
        sev = SEVERITY_FACTOR.get(v.severity, 1.0)
        total += weight * sev
    return total


def penalty_to_score_delta(
    penalty: float,
    *,
    scale: float | None = None,
    policy: BannedTokenPolicy | None = None,
) -> float:
    """Convert a non-negative penalty into a (negative) score delta.

    By default the scale comes from the policy's ``grader_score_scale``
    (10.0 in the bundled defaults), so a unit-weight error hit moves the
    final score by ``-0.1``.
    """
    if scale is None:
        scale = policy.grader_score_scale if policy is not None else 10.0
    if scale <= 0:
        scale = 1.0
    return -1.0 * float(penalty) / float(scale)


def apply_to_score(
    score: float,
    penalty: float,
    *,
    scale: float | None = None,
    policy: BannedTokenPolicy | None = None,
    floor: float = 0.0,
) -> float:
    """Apply a penalty to ``score`` and clamp at ``floor`` (default 0)."""
    delta = penalty_to_score_delta(penalty, scale=scale, policy=policy)
    return max(float(floor), float(score) + delta)
