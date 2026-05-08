"""RL reward-shaping helper.

Given a model completion (or any text), return a non-negative penalty
to subtract from the RL reward. The penalty is identical in spirit to
the grader penalty but does not require building a
``MonitorViolationReport``: it scans the text directly with the shared
matcher and aggregates ``weight * severity_factor`` over all hits.
"""

from __future__ import annotations

from chomsky_vv.banned.matcher import BannedTokenMatcher
from chomsky_vv.banned.penalty import SEVERITY_FACTOR
from chomsky_vv.banned.policy import BannedTokenPolicy, default_policy


def banned_reward_penalty(
    text: str,
    policy: BannedTokenPolicy | None = None,
    *,
    lambda_: float | None = None,
) -> float:
    """Return ``lambda * sum(weight * severity_factor)`` over hits in ``text``.

    The returned penalty is non-negative; subtract it from your RL
    reward (e.g. ``reward -= banned_reward_penalty(completion)``).
    Defaults follow ``policy.rl_lambda`` (1.0 in the bundled defaults).
    """
    pol = policy or default_policy()
    if lambda_ is None:
        lambda_ = pol.rl_lambda
    matcher = BannedTokenMatcher(pol)
    hits = matcher.scan_text(text, "<reward>")
    if not hits:
        return 0.0
    total = 0.0
    for h in hits:
        total += pol.weight_for(h.token) * SEVERITY_FACTOR.get(h.severity, 1.0)
    return float(lambda_) * total
