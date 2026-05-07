"""Smoke tests for the PaperBench Chomsky V&V wiring.

These tests cover the import-light pieces (alphabet, contracts, bridge,
log discovery) and a full producer/consumer pipeline run that bypasses
the live Monitor by feeding a synthetic MonitorResult through the
bridge. The gate's network/disk side (paper_registry blacklist load) is
out of scope here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chomsky_vv import ChomskyClass, ProbeHarness, ProbeVerdict, TraceRecorder
from paperbench.chomsky import (
    classification_for,
    default_classifications,
    find_agent_log,
    monitor_result_to_violation_report,
    paperbench_default_alphabet,
)
from paperbench.monitor.monitor import MonitorResult, ViolationContext


def test_alphabet_contains_canonical_tokens() -> None:
    a = paperbench_default_alphabet()
    assert "bash" in a.names
    assert "python" in a.names
    assert "judge_push" in a.names
    assert "judge_pop" in a.names
    assert a.by_name("judge_push").push is True
    assert a.by_name("judge_pop").pop is True
    assert a.by_name("judge_pop").pairs_with == "judge_push"


def test_default_classifications_cover_expected_agents() -> None:
    classifications = default_classifications()
    expected = {
        "pb.basicagent",
        "pb.iterative_agent",
        "pb.dummy",
        "pb.direct_submission",
        "pb.human",
        "pb.simple_judge",
        "pb.dummy_judge",
        "pb.random_judge",
        "pb.monitor",
    }
    assert set(classifications.keys()) == expected
    assert classifications["pb.basicagent"].predicted_chomsky_class == ChomskyClass.TYPE_0
    assert classifications["pb.simple_judge"].predicted_chomsky_class == ChomskyClass.TYPE_2
    assert classifications["pb.dummy"].predicted_chomsky_class == ChomskyClass.TYPE_3


def test_classification_for_unknown_raises() -> None:
    with pytest.raises(KeyError):
        classification_for("pb.does_not_exist")


def test_monitor_bridge_translates_violations() -> None:
    result = MonitorResult(
        violations=[
            ViolationContext(
                line_number=10,
                violation="forbidden.example",
                context=["a", "b", "git clone https://forbidden.example/repo", "d"],
                context_start=8,
            )
        ],
        explanation="found 1",
        log_file="/tmp/agent.log",
    )
    report = monitor_result_to_violation_report(
        result=result, agent_id="pb.basicagent", run_id="r1"
    )
    assert report.has_blocking_violation is True
    assert report.violations[0].rule_id == "forbidden.example"
    assert "forbidden.example" in report.violations[0].excerpt


def test_find_agent_log_locates_nested_log(tmp_path: Path) -> None:
    log = tmp_path / "submissions" / "stamp" / "logs" / "agent.log"
    log.parent.mkdir(parents=True)
    log.write_text("BashTool.execute step\n", encoding="utf-8")
    found = find_agent_log(tmp_path)
    assert found is not None
    assert found.read_text().startswith("BashTool.execute")


def test_find_agent_log_returns_none_when_absent(tmp_path: Path) -> None:
    assert find_agent_log(tmp_path) is None


def test_producer_consumer_pipeline_blocks_on_certifier_violation(tmp_path: Path) -> None:
    """Full pipeline: TraceRecorder + Monitor bridge → ProbeHarness."""
    log = tmp_path / "agent.log"
    log.write_text(
        "BashTool.execute step 1\nPythonTool.execute step 2\n[reminder] step 3\n",
        encoding="utf-8",
    )
    contract = classification_for("pb.basicagent")
    alphabet = paperbench_default_alphabet()
    recorder = TraceRecorder(agent_id=contract.agent_id, run_id="r1", alphabet=alphabet)
    recorder.record_text(log.read_text(), source_ref=str(log))
    trace = recorder.trace()
    assert any(t.token == "bash" for t in trace.tokens)
    assert any(t.token == "python" for t in trace.tokens)

    monitor_result = MonitorResult(
        violations=[
            ViolationContext(
                line_number=2,
                violation="forbidden.example",
                context=["git clone https://forbidden.example/x"],
                context_start=2,
            )
        ],
        explanation="blacklist hit",
        log_file=str(log),
    )
    report = monitor_result_to_violation_report(
        result=monitor_result, agent_id=contract.agent_id, run_id="r1"
    )
    validation = ProbeHarness(alphabet=alphabet).run(
        contract=contract, trace=trace, monitor_report=report
    )
    assert validation.blocked is True
    assert validation.overall_verdict == ProbeVerdict.FAIL


def test_producer_consumer_pipeline_passes_clean_run(tmp_path: Path) -> None:
    log = tmp_path / "agent.log"
    log.write_text("BashTool.execute step 1\nSubmitTool finished\n", encoding="utf-8")
    contract = classification_for("pb.basicagent")
    alphabet = paperbench_default_alphabet()
    recorder = TraceRecorder(agent_id=contract.agent_id, run_id="r2", alphabet=alphabet)
    recorder.record_text(log.read_text())
    monitor_result = MonitorResult(violations=[], explanation="clean", log_file=str(log))
    report = monitor_result_to_violation_report(
        result=monitor_result, agent_id=contract.agent_id, run_id="r2"
    )
    validation = ProbeHarness(alphabet=alphabet).run(
        contract=contract, trace=recorder.trace(), monitor_report=report
    )
    assert validation.blocked is False
    # Type-0 contract: P1/P2/P3/P6 all skip; P4 inconclusive without multi-trace; pipeline is PASS.
    assert validation.overall_verdict == ProbeVerdict.PASS
