"""Word-boundary text matcher: domain + literal + word kinds."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from chomsky_vv.banned import BannedTokenMatcher, default_policy


def _scan(source: str) -> list[str]:
    matcher = BannedTokenMatcher(default_policy())
    hits = matcher.scan_text(source, "<inline.md>")
    return [f"{h.token}" for h in hits]


def test_example_com_matches_only_with_proper_boundary() -> None:
    src = "Visit example.com for details, but not myexample.com or example.community."
    hits = _scan(src)
    assert hits == ["example.com"]


def test_api_key_literal_with_word_boundaries() -> None:
    src = "Set API_KEY=abc but ignore MY_API_KEY_HASH or API_KEYRING."
    hits = _scan(src)
    assert hits == ["API_KEY"]


def test_train_word_does_not_match_inside_underscore_identifier() -> None:
    src = "Use X_train and y_train then call train_test_split."
    assert _scan(src) == []


def test_train_word_matches_in_prose() -> None:
    src = "We will train the model and then test it."
    hits = _scan(src)
    assert "train" in hits
    assert "test" in hits


def test_secret_password_in_yaml_like_text() -> None:
    src = "credentials:\n  secret: shh\n  password: hunter2\n"
    hits = _scan(src)
    assert "secret" in hits
    assert "password" in hits


def test_mocking_word_does_not_match_mock() -> None:
    src = "We are mocking the upstream call."
    assert _scan(src) == []


def test_mock_word_matches_when_isolated() -> None:
    src = "Insert a mock here."
    assert _scan(src) == ["mock"]


def test_dummy_allowlisted_in_text() -> None:
    src = "Use the dummy agent."
    assert _scan(src) == []
