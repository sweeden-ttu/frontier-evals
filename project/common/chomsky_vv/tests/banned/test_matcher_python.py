"""Python AST/identifier-aware matcher: false-positive + true-positive coverage."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from chomsky_vv.banned import BannedTokenMatcher, default_policy


def _scan(source: str) -> list[str]:
    matcher = BannedTokenMatcher(default_policy())
    hits = matcher.scan_python(source, "<inline.py>")
    return [f"{h.token}:{h.kind}:{h.line}" for h in hits]


# ---------------------------------------------------------------- false positives
def test_train_test_split_does_not_match() -> None:
    src = "from sklearn.model_selection import train_test_split\n"
    assert _scan(src) == []


def test_pretrain_and_pytest_do_not_match() -> None:
    src = "def pretrain_model(): pass\nimport pytest as _pt\n"
    assert _scan(src) == []


def test_substring_identifiers_are_safe() -> None:
    src = "x_train = 1\nlatest = 2\nattestation = 'ok'\nclass Pretrainer:\n    pass\n"
    assert _scan(src) == []


def test_dunder_main_does_not_match() -> None:
    src = "if __name__ == '__main__':\n    pass\n"
    assert _scan(src) == []


def test_allowlisted_dummy_identifier_skipped() -> None:
    src = "agent_id = 'dummy'\n"
    assert _scan(src) == []


# ---------------------------------------------------------------- true positives
def test_function_named_train_fires() -> None:
    src = "def train():\n    return 1\n"
    hits = _scan(src)
    assert any(h.startswith("train:identifier:") for h in hits)


def test_password_string_literal_fires() -> None:
    src = 'password = "hunter2"\n'
    hits = _scan(src)
    assert any(h.startswith("password:identifier:") for h in hits)


def test_mock_in_comment_fires() -> None:
    src = "x = 1  # TODO: mock this later\n"
    hits = _scan(src)
    assert any(h.startswith("mock:comment:") for h in hits)


def test_synthetic_in_docstring_fires() -> None:
    src = '"""runs a synthetic test"""\n'
    hits = _scan(src)
    tokens = {h.split(":")[0] for h in hits}
    assert "synthetic" in tokens
    assert "test" in tokens


def test_api_key_literal_in_string_fires() -> None:
    src = 'header = "Authorization: API_KEY"\n'
    hits = _scan(src)
    assert any(h.startswith("API_KEY:") for h in hits)


def test_example_dot_com_in_string_fires() -> None:
    src = 'url = "https://example.com/path"\n'
    hits = _scan(src)
    assert any(h.startswith("example.com:") for h in hits)


def test_api_key_negative_in_extended_identifier() -> None:
    src = 'token = "MY_API_KEY_HASH"\n'
    hits = _scan(src)
    assert hits == []


def test_class_named_test_fires() -> None:
    src = "class test:\n    pass\n"
    hits = _scan(src)
    assert any(h.startswith("test:identifier:") for h in hits)


def test_argument_named_secret_fires() -> None:
    src = "def login(secret):\n    return secret\n"
    hits = _scan(src)
    assert any(h.startswith("secret:identifier:") for h in hits)
