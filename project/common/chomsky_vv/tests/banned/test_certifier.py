"""End-to-end: BannedTokenCertifier → MonitorCertifierProbe wiring."""

from __future__ import annotations

from pathlib import Path

# pyrefly: ignore [missing-import]
from chomsky_vv import (
    Alphabet,
    BannedTokenCertifier,
    ChomskyClass,
    ChomskyClassification,
    MemoryHypothesis,
    ProbeVerdict,
    TokenSpec,
    TraceRecord,
    VVObligationBudget,
)

# pyrefly: ignore [missing-import]
from chomsky_vv.probes.monitor_certifier import MonitorCertifierProbe


def _alphabet() -> Alphabet:
    return Alphabet(tokens=[TokenSpec(name="bash", pattern=r"BASH")])


def _empty_trace(agent: str = "pb.banned") -> TraceRecord:
    return TraceRecord(agent_id=agent, run_id="r1", tokens=[])


def _contract() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.banned",
        source_paths=["x.py"],
        sigma_trace_alphabet_encoding=["bash"],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="none"),
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=8,
            test_case_count=4,
            judge_call_budget=2,
        ),
    )


def test_dirty_dir_blocks_via_monitor_certifier(tmp_path: Path) -> None:
    src = tmp_path / "agent.py"
    src.write_text(
        'def train():\n'
        '    password = "hunter2"\n'
        '    return password\n',
        encoding="utf-8",
    )
    certifier = BannedTokenCertifier(agent_id="pb.banned", run_id="r1")
    report = certifier.scan(tmp_path)
    assert report.has_blocking_violation is True
    assert any(v.rule_id == "banned:train" for v in report.violations)
    assert any(v.rule_id == "banned:password" for v in report.violations)

    probe = MonitorCertifierProbe()
    result = probe.run(
        contract=_contract(),
        trace=_empty_trace(),
        alphabet=_alphabet(),
        monitor_report=report,
    )
    assert result.verdict is ProbeVerdict.FAIL
    assert result.refutes_class is ChomskyClass.TYPE_3


def test_clean_dir_passes(tmp_path: Path) -> None:
    src = tmp_path / "agent.py"
    src.write_text(
        "def fit(features, labels):\n"
        "    return features.shape, labels.shape\n",
        encoding="utf-8",
    )
    certifier = BannedTokenCertifier(agent_id="pb.banned", run_id="r1")
    report = certifier.scan(tmp_path)
    assert report.has_blocking_violation is False
    assert report.violations == []

    probe = MonitorCertifierProbe()
    result = probe.run(
        contract=_contract(),
        trace=_empty_trace(),
        alphabet=_alphabet(),
        monitor_report=report,
    )
    assert result.verdict is ProbeVerdict.PASS


def test_text_only_input_routed_through_certifier() -> None:
    certifier = BannedTokenCertifier(agent_id="pb.banned", run_id="r1")
    report = certifier.scan_text("API_KEY=abc and password=def", ref="<inline>")
    rules = {v.rule_id for v in report.violations}
    assert "banned:API_KEY" in rules
    assert "banned:password" in rules
