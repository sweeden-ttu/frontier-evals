"""``chomsky-banned`` CLI: scan exits non-zero on hits, zero on clean trees."""

from __future__ import annotations

import json
from pathlib import Path

# pyrefly: ignore [missing-import]
from chomsky_vv.banned.cli import main


def test_cli_scan_returns_nonzero_on_error_severity_hit(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text('password = "hunter2"\n', encoding="utf-8")
    code = main(["scan", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 1
    assert "password" in captured.out


def test_cli_scan_returns_zero_on_clean_tree(tmp_path: Path) -> None:
    clean = tmp_path / "ok.py"
    clean.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    code = main(["scan", str(tmp_path)])
    assert code == 0


def test_cli_scan_json_output_is_parseable(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("def train():\n    return 1\n", encoding="utf-8")
    main(["scan", "--json", str(tmp_path)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["n_hits"] >= 1
    assert any(h["token"] == "train" for h in payload["hits"])


def test_cli_check_subcommand_always_nonzero_on_hit(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("API_KEY=abc\n", encoding="utf-8")
    code = main(["check", str(bad)])
    assert code == 1


def test_cli_init_writes_default_policy(tmp_path: Path) -> None:
    out = tmp_path / "policy.yaml"
    code = main(["init", "--out", str(out)])
    assert code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "tokens:" in content
    assert "API_KEY" in content


def test_cli_init_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    out = tmp_path / "policy.yaml"
    out.write_text("placeholder\n", encoding="utf-8")
    code = main(["init", "--out", str(out)])
    assert code == 1
    assert out.read_text(encoding="utf-8") == "placeholder\n"


def test_cli_exit_nonzero_on_hit_flag(tmp_path: Path) -> None:
    # Build a policy with a warn-only hit, then ensure --exit-nonzero-on-hit
    # forces exit code 1 even though no error-severity hit is present.
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        "tokens:\n"
        "  - token: foobar\n"
        "    severity: warn\n"
        "    match_kind: word\n"
        "    weight: 1.0\n"
        "allowlist_identifiers: []\n"
        "per_extension_overrides: {}\n"
        "weights: {}\n"
        "grader_score_scale: 10.0\n"
        "logits_soft_penalty: -50.0\n"
        "logits_hard_mode: false\n"
        "rl_lambda: 1.0\n",
        encoding="utf-8",
    )
    bad = tmp_path / "bad.txt"
    bad.write_text("hello foobar\n", encoding="utf-8")
    code_default = main(["scan", "--policy", str(policy_path), str(bad)])
    code_force = main(
        ["scan", "--policy", str(policy_path), "--exit-nonzero-on-hit", str(bad)]
    )
    assert code_default == 0
    assert code_force == 1
