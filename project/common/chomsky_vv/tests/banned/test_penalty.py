"""Penalty arithmetic + score-delta clamping."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from chomsky_vv.banned import (
    BannedToken,
    BannedTokenPolicy,
    apply_to_score,
    compute_penalty,
    default_policy,
    penalty_to_score_delta,
)
# pyrefly: ignore [missing-import]
from chomsky_vv.schemas import MonitorViolation, MonitorViolationReport


def _report(*tokens: tuple[str, str]) -> MonitorViolationReport:
    return MonitorViolationReport(
        agent_id="a",
        run_id="r",
        monitor_id="m",
        violations=[
            MonitorViolation(rule_id=f"banned:{t}", severity=sev) for t, sev in tokens
        ],
    )


def test_compute_penalty_default_weights() -> None:
    pol = default_policy()
    rep = _report(("train", "error"), ("password", "error"))
    assert compute_penalty(rep, pol) == 2.0


def test_compute_penalty_severity_factors() -> None:
    pol = default_policy()
    rep = _report(("train", "warn"), ("password", "info"))
    assert abs(compute_penalty(rep, pol) - (0.4 + 0.1)) < 1e-9


def test_compute_penalty_custom_weights() -> None:
    pol = BannedTokenPolicy(
        tokens=[
            BannedToken(token="train", severity="error", match_kind="word", weight=3.0),
            BannedToken(token="password", severity="error", match_kind="word", weight=2.0),
        ],
    )
    rep = _report(("train", "error"), ("password", "error"))
    assert compute_penalty(rep, pol) == 5.0


def test_weights_dict_overrides_token_weight() -> None:
    pol = BannedTokenPolicy(
        tokens=[
            BannedToken(token="train", severity="error", match_kind="word", weight=1.0),
        ],
        weights={"train": 7.5},
    )
    rep = _report(("train", "error"))
    assert compute_penalty(rep, pol) == 7.5


def test_score_delta_default_scale_is_ten() -> None:
    delta = penalty_to_score_delta(2.0, policy=default_policy())
    assert abs(delta - (-0.2)) < 1e-9


def test_score_delta_explicit_scale() -> None:
    delta = penalty_to_score_delta(5.0, scale=2.0)
    assert delta == -2.5


def test_apply_to_score_clamps_at_zero() -> None:
    final = apply_to_score(0.05, penalty=10.0, scale=10.0)
    assert final == 0.0


def test_apply_to_score_unaffected_when_no_penalty() -> None:
    final = apply_to_score(0.7, penalty=0.0)
    assert final == 0.7
