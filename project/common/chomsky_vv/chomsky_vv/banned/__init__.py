"""Banned-token punisher subpackage.

Public API for the canonical banned-token registry, AST-aware matcher,
non-LLM certifier, grader penalty arithmetic, and (optional) inference-
time logits processor + RL reward shaper.

The matcher is identifier-aware: bare Python identifiers must equal a
banned token exactly, and word-boundary regex (``\\b``) is used for
string literals/comments/docstrings/text. Allowlist exemptions are
applied after a candidate hit so projects can opt out of specific
collisions (e.g. the ``dummy`` agent id used by mle-bench) without
removing the token from the registry.
"""

from chomsky_vv.banned.certifier import BannedTokenCertifier
from chomsky_vv.banned.matcher import BannedTokenMatcher, Hit
from chomsky_vv.banned.penalty import (
    apply_to_score,
    compute_penalty,
    penalty_to_score_delta,
)
from chomsky_vv.banned.policy import (
    BannedToken,
    BannedTokenPolicy,
    default_policy,
    load_policy,
)
from chomsky_vv.banned.reward import (
    POSITIVE_REWARD_TERMS,
    banned_reward_penalty,
    net_reward_adjustment,
    positive_scheme_reward,
)

__all__ = [
    "BannedToken",
    "BannedTokenCertifier",
    "BannedTokenMatcher",
    "BannedTokenPolicy",
    "Hit",
    "POSITIVE_REWARD_TERMS",
    "apply_to_score",
    "banned_reward_penalty",
    "compute_penalty",
    "default_policy",
    "load_policy",
    "net_reward_adjustment",
    "penalty_to_score_delta",
    "positive_scheme_reward",
]
