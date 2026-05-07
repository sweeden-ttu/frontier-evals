"""Smoke tests for evmbench Chomsky V&V wiring.

These tests cover the import-light pieces — alphabet, contract registry,
veto bridge, and a synthetic producer→consumer pipeline run that does
not require live containers, alcatraz, or a real Veto sidecar.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chomsky_vv import ChomskyClass, ProbeHarness, ProbeVerdict, TraceRecorder
from evmbench.chomsky import (
    classification_for,
    default_classifications,
    evmbench_default_alphabet,
    scan_veto_log,
)


def test_alphabet_matches_real_solver_log_lines() -> None:
    """The chomsky-agent's regex defaults are useless if they don't match
    the actual ``ctx_logger.info`` strings emitted by evmbench. This test
    pins the regex set against representative log lines lifted from the
    source."""
    a = evmbench_default_alphabet()
    samples = [
        ("[some-audit-id] Starting detect iteration 1/3", "evm_iter_start"),
        ("[some-audit-id] Completed detect iteration 1/3", "evm_iter_complete"),
        ("[some-audit-id] Failed to download audit report after iteration 2: oops", "evm_iter_failed"),
        ("Started Veto proxy.", "evm_veto_started"),
        ("Stopped Veto proxy.", "evm_veto_stopped"),
        ("Agent finished successfully.", "evm_agent_finished"),
        ("Run failed with error: boom", "evm_agent_failed"),
        ("Waiting for agent to finish... (elapsed: 12s)", "evm_agent_waiting"),
        ("Run completed in 42.5 seconds.", "evm_agent_complete"),
        ("Starting computer. This may take a while...", "evm_starting_computer"),
    ]
    for line, expected in samples:
        rec = TraceRecorder(agent_id="t", run_id="t", alphabet=a)
        rec.record_text(line)
        names = [t.token for t in rec.trace().tokens]
        assert expected in names, f"{expected!r} not matched in {line!r}; got {names}"


def test_default_classifications_cover_inventory() -> None:
    classifications = default_classifications()
    expected = {
        "evm.solver",
        "evm.external_agents.claude",
        "evm.external_agents.codex",
        "evm.external_agents.gemini",
        "evm.external_agents.opencode",
        "evm.veto",
        "evm.detect_grader",
        "evm.patch_grader",
        "evm.exploit_grader",
    }
    assert set(classifications.keys()) == expected
    assert classifications["evm.solver"].predicted_chomsky_class == ChomskyClass.TYPE_0
    assert classifications["evm.veto"].predicted_chomsky_class == ChomskyClass.TYPE_3
    assert classifications["evm.patch_grader"].predicted_chomsky_class == ChomskyClass.TYPE_2


def test_classification_for_unknown_raises() -> None:
    with pytest.raises(KeyError):
        classification_for("evm.does_not_exist")


def test_veto_bridge_extracts_blocking_violations(tmp_path: Path) -> None:
    log = tmp_path / "veto.log"
    log.write_text(
        "[veto] accept method=eth_call host=api.openai.com\n"
        "[veto] denied method=eth_sendRawTransaction sni_violation host=evil.example\n"
        "[veto] blocked method=admin_addPeer method_not_allowed\n"
        "[veto] chain_id_mismatch expected=1 actual=137\n"
        "[veto] heartbeat ok\n",
        encoding="utf-8",
    )
    report = scan_veto_log(
        log_path=log, agent_id="evm.solver", run_id="r1", monitor_id="evmbench.veto"
    )
    rule_ids = [v.rule_id for v in report.violations]
    assert "sni_violation" in rule_ids
    assert "method_not_allowed" in rule_ids
    assert "chainid_mismatch" in rule_ids
    assert report.has_blocking_violation is True


def test_veto_bridge_clean_log(tmp_path: Path) -> None:
    log = tmp_path / "veto.log"
    log.write_text(
        "[veto] accept method=eth_call host=api.openai.com\n"
        "[veto] heartbeat ok\n",
        encoding="utf-8",
    )
    report = scan_veto_log(log_path=log, agent_id="evm.solver", run_id="r1")
    assert len(report.violations) == 0
    assert report.has_blocking_violation is False


def test_producer_consumer_pipeline_blocks_on_veto_violation(tmp_path: Path) -> None:
    log = tmp_path / "agent.log"
    log.write_text(
        "[audit-x] Starting detect iteration 1/3\n"
        "Started Veto proxy.\n"
        "Agent finished successfully.\n"
        "[audit-x] Completed detect iteration 1/3\n",
        encoding="utf-8",
    )
    veto_log = tmp_path / "veto.log"
    veto_log.write_text(
        "[veto] denied method=admin_addPeer method_not_allowed\n",
        encoding="utf-8",
    )
    contract = classification_for("evm.solver")
    alphabet = evmbench_default_alphabet()
    rec = TraceRecorder(agent_id=contract.agent_id, run_id="r1", alphabet=alphabet)
    rec.record_text(log.read_text())
    veto_report = scan_veto_log(
        log_path=veto_log, agent_id=contract.agent_id, run_id="r1"
    )
    validation = ProbeHarness(alphabet=alphabet).run(
        contract=contract, trace=rec.trace(), monitor_report=veto_report
    )
    assert validation.blocked is True
    assert validation.overall_verdict == ProbeVerdict.FAIL


def test_producer_consumer_pipeline_passes_clean_run(tmp_path: Path) -> None:
    log = tmp_path / "agent.log"
    log.write_text(
        "[audit-y] Starting detect iteration 1/2\n"
        "Started Veto proxy.\n"
        "Agent finished successfully.\n"
        "Stopped Veto proxy.\n"
        "[audit-y] Completed detect iteration 1/2\n",
        encoding="utf-8",
    )
    veto_log = tmp_path / "veto.log"
    veto_log.write_text("[veto] heartbeat ok\n", encoding="utf-8")
    contract = classification_for("evm.solver")
    alphabet = evmbench_default_alphabet()
    rec = TraceRecorder(agent_id=contract.agent_id, run_id="r2", alphabet=alphabet)
    rec.record_text(log.read_text())
    veto_report = scan_veto_log(
        log_path=veto_log, agent_id=contract.agent_id, run_id="r2"
    )
    validation = ProbeHarness(alphabet=alphabet).run(
        contract=contract, trace=rec.trace(), monitor_report=veto_report
    )
    assert validation.blocked is False
    assert validation.overall_verdict == ProbeVerdict.PASS
