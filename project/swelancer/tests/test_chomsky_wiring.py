"""Smoke tests for swelancer Chomsky V&V wiring.

Covers the import-light pieces: alphabet, contract registry, NEW
non-LLM certifier (test-bundle isolation envelope + python-block CFG
validator), and a producer→consumer pipeline run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chomsky_vv import ChomskyClass, ProbeHarness, ProbeVerdict, TraceRecorder
from swelancer.chomsky import (
    CertifierMode,
    SwelancerCertifier,
    classification_for,
    default_classifications,
    python_block_cfg_validator,
    swelancer_default_alphabet,
    verify_test_bundle_isolation,
)


def test_alphabet_matches_real_solver_log_lines() -> None:
    a = swelancer_default_alphabet()
    samples = [
        ("Starting computer...", "swe_starting_computer"),
        ("Trimming message...", "swe_trim_message"),
        ("Message history on turn 39, number of messages: 4: [{'role': 'user', 'content': 'hi'}]", "swe_message_history"),
        ("Message history on turn 39, number of messages: 4: [{'role': 'user', 'content': 'hi'}]", "swe_role_user"),
        ("User tool call detected", "swe_user_tool_detected"),
        ("No user tool call detected; executing code", "swe_user_tool_not_detected"),
        ("Agent code timed out", "swe_agent_timeout"),
        ("```python\nprint(1)\n```", "swe_python_block_open"),
        ("the model said <user-tool>", "swe_user_tool_open"),
        ("the model closed </user-tool>", "swe_user_tool_close"),
    ]
    for line, expected in samples:
        rec = TraceRecorder(agent_id="t", run_id="t", alphabet=a)
        rec.record_text(line)
        names = [t.token for t in rec.trace().tokens]
        assert expected in names, f"{expected!r} not matched in {line!r}; got {names}"


def test_default_classifications_cover_inventory() -> None:
    classifications = default_classifications()
    assert set(classifications.keys()) == {"swe.simple_agent", "swe.dummy"}
    # swe.simple_agent: Type-0 envelope (embeds Type-0 island via python -c)
    assert classifications["swe.simple_agent"].predicted_chomsky_class == ChomskyClass.TYPE_0
    assert classifications["swe.dummy"].predicted_chomsky_class == ChomskyClass.TYPE_3


def test_classification_for_unknown_raises() -> None:
    with pytest.raises(KeyError):
        classification_for("swe.does_not_exist")


def test_python_block_cfg_validator_rejects_subprocess() -> None:
    code = "import subprocess\nsubprocess.run(['ls'])\n"
    violations = python_block_cfg_validator(code=code)
    rule_ids = {v.rule_id for v in violations}
    assert "forbidden_import:subprocess" in rule_ids
    assert "forbidden_attr_call:run" in rule_ids
    assert all(v.severity == "error" for v in violations)


def test_python_block_cfg_validator_rejects_eval_exec() -> None:
    code = "eval('1+1')\nexec('print(2)')\ncompile('x', '<x>', 'exec')\n"
    violations = python_block_cfg_validator(code=code)
    rule_ids = {v.rule_id for v in violations}
    assert "forbidden_call:eval" in rule_ids
    assert "forbidden_call:exec" in rule_ids
    assert "forbidden_call:compile" in rule_ids


def test_python_block_cfg_validator_rejects_attribute_chain() -> None:
    code = "import os\nos.system('ls')\n"
    violations = python_block_cfg_validator(code=code)
    rule_ids = {v.rule_id for v in violations}
    assert "forbidden_import:os" in rule_ids
    assert "forbidden_attr_call:system" in rule_ids


def test_python_block_cfg_validator_accepts_safe_code() -> None:
    code = "x = 1 + 2\nprint(x)\nfor i in range(3):\n    pass\n"
    violations = python_block_cfg_validator(code=code)
    assert violations == []


def test_python_block_cfg_validator_advisory_severity() -> None:
    code = "import os"
    violations = python_block_cfg_validator(code=code, mode=CertifierMode.ADVISORY)
    assert all(v.severity == "warn" for v in violations)


def test_python_block_cfg_validator_handles_syntax_error() -> None:
    code = "def broken(:\n"
    violations = python_block_cfg_validator(code=code)
    assert len(violations) == 1
    assert violations[0].rule_id == "python_block_syntax_error"


def test_test_bundle_isolation_passes_for_clean_log() -> None:
    log = (
        "Starting computer...\n"
        "User tool call detected\n"
        "<user-tool>\n"
        "tool ran ok\n"
        "</user-tool>\n"
        "rm -rf /app/tests done\n"
    )
    violations = verify_test_bundle_isolation(log_text=log)
    assert violations == []


def test_test_bundle_isolation_detects_password_leak() -> None:
    log = "User tool call detected\nleaked: secretpasswordhere\n"
    violations = verify_test_bundle_isolation(log_text=log)
    rule_ids = {v.rule_id for v in violations}
    assert "password_leak" in rule_ids


def test_test_bundle_isolation_detects_unbalanced_user_tool() -> None:
    log = "<user-tool>\nbut never closed\n"
    violations = verify_test_bundle_isolation(log_text=log)
    rule_ids = {v.rule_id for v in violations}
    assert "user_tool_unbalanced" in rule_ids


def test_test_bundle_isolation_detects_post_rm_test_reference() -> None:
    log = (
        "<user-tool>\n"
        "</user-tool>\n"
        "rm -rf /app/tests\n"
        "ls /app/tests\n"
    )
    violations = verify_test_bundle_isolation(log_text=log)
    rule_ids = {v.rule_id for v in violations}
    assert "test_bundle_escape" in rule_ids


def test_swelancer_certifier_full_log_scan(tmp_path: Path) -> None:
    log = tmp_path / "agent.log"
    log.write_text("User tool call detected\nleaked: secretpasswordhere\n", encoding="utf-8")
    certifier = SwelancerCertifier(agent_id="swe.simple_agent", run_id="r1")
    report = certifier.scan_log(log)
    assert report.has_blocking_violation is True
    assert any(v.rule_id == "password_leak" for v in report.violations)


def test_producer_consumer_pipeline_blocks_on_certifier_violation(tmp_path: Path) -> None:
    log = tmp_path / "agent.log"
    log.write_text(
        "Starting computer...\n"
        "Message history on turn 39, number of messages: 1: [{'role': 'user', 'content': 'hi'}]\n"
        "User tool call detected\n"
        "leaked: secretpasswordhere\n",
        encoding="utf-8",
    )
    contract = classification_for("swe.simple_agent")
    alphabet = swelancer_default_alphabet()
    rec = TraceRecorder(agent_id=contract.agent_id, run_id="r1", alphabet=alphabet)
    rec.record_text(log.read_text())
    certifier = SwelancerCertifier(
        agent_id=contract.agent_id, run_id="r1", mode=CertifierMode.ENFORCING
    )
    monitor_report = certifier.scan_log(log)
    validation = ProbeHarness(alphabet=alphabet).run(
        contract=contract, trace=rec.trace(), monitor_report=monitor_report
    )
    assert validation.blocked is True
    assert validation.overall_verdict == ProbeVerdict.FAIL
