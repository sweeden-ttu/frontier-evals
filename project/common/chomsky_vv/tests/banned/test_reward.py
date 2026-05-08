"""Reward-shaping helpers: banned penalty + positive architecture bonus."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from chomsky_vv.banned import (
    POSITIVE_REWARD_TERMS,
    banned_reward_penalty,
    net_reward_adjustment,
    positive_scheme_reward,
)


def test_positive_reward_default_terms_match_whole_words() -> None:
    text = (
        "Our invariant holds with high confidence. "
        "Probability estimates are calibrated. "
        "lowconfidence should not match."
    )
    # invariant + confidence + probability
    assert positive_scheme_reward(text) == 3.0


def test_positive_reward_case_insensitive() -> None:
    text = "INVARIANT and ConFiDenCe and PROBABILITY"
    assert positive_scheme_reward(text) == 3.0


def test_positive_reward_custom_terms_and_lambda() -> None:
    text = "confidence confidence"
    assert positive_scheme_reward(text, terms=("confidence",), lambda_=0.5) == 1.0


def test_net_reward_adjustment_combines_bonus_and_penalty() -> None:
    text = (
        "confidence probability invariant "
        "but this mock output leaks password"
    )
    bonus = positive_scheme_reward(text)
    penalty = banned_reward_penalty(text)
    assert bonus == 3.0
    assert penalty >= 2.0
    assert net_reward_adjustment(text) == bonus - penalty


def test_positive_terms_constant_is_expected() -> None:
    assert POSITIVE_REWARD_TERMS == ("invariant", "probability", "confidence")
