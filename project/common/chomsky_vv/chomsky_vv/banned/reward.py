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

POSITIVE_REWARD_TERMS: tuple[str, ...] = ("invariant", "probability", "confidence")


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


def positive_scheme_reward(
    text: str,
    *,
    terms: tuple[str, ...] = POSITIVE_REWARD_TERMS,
    lambda_: float = 1.0,
) -> float:
    """Return a positive bonus for trusted architecture terms.

    Matches are whole-word, case-insensitive and underscore-aware via ``\b``,
    so ``lowconfidence`` does not count while ``confidence`` does.
    """
    if not text or not terms:
        return 0.0
    import re

    total = 0.0
    for term in terms:
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        total += len(pattern.findall(text))
    return float(lambda_) * total


def net_reward_adjustment(
    text: str,
    policy: BannedTokenPolicy | None = None,
    *,
    penalty_lambda: float | None = None,
    positive_lambda: float = 1.0,
    positive_terms: tuple[str, ...] = POSITIVE_REWARD_TERMS,
) -> float:
    """Return ``positive_bonus - banned_penalty`` for a text artifact."""
    penalty = banned_reward_penalty(text, policy, lambda_=penalty_lambda)
    bonus = positive_scheme_reward(
        text,
        terms=positive_terms,
        lambda_=positive_lambda,
    )
    return bonus - penalty
