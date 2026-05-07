from __future__ import annotations

from chomsky_vv import (
    Alphabet,
    ChomskyClass,
    ChomskyClassification,
    MemoryHypothesis,
    ProbeHarness,
    ProbeVerdict,
    TokenSpec,
    TraceRecorder,
    VVObligationBudget,
)
from chomsky_vv.adapters import monitor_blacklist_to_violations


def _bracket_alphabet() -> Alphabet:
    return Alphabet(
        tokens=[
            TokenSpec(name="round_open", pattern=r"\(", push=True),
            TokenSpec(name="round_close", pattern=r"\)", pop=True, pairs_with="round_open"),
            TokenSpec(name="square_open", pattern=r"\[", push=True),
            TokenSpec(name="square_close", pattern=r"\]", pop=True, pairs_with="square_open"),
            TokenSpec(name="bash", pattern=r"BASH"),
        ]
    )


def _contract(cls: ChomskyClass, agent_id: str = "pb.test") -> ChomskyClassification:
    return ChomskyClassification(
        agent_id=agent_id,
        source_paths=["dummy.py"],
        sigma_trace_alphabet_encoding=["round_open", "round_close", "bash"],
        predicted_chomsky_class=cls,
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="none"),
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=10, test_case_count=10, judge_call_budget=0
        ),
    )


def _trace_from(text: str, alphabet: Alphabet, agent: str, run: str = "r1"):
    rec = TraceRecorder(agent_id=agent, run_id=run, alphabet=alphabet)
    rec.record_text(text)
    return rec.trace()


def test_type3_passes_on_flat_trace() -> None:
    a = _bracket_alphabet()
    trace = _trace_from("BASH BASH BASH", a, agent="pb.flat")
    contract = _contract(ChomskyClass.TYPE_3)
    report = ProbeHarness(alphabet=a).run(contract=contract, trace=trace)
    assert report.overall_verdict == ProbeVerdict.PASS
    p1 = next(r for r in report.probe_results if r.probe_id == "P1")
    assert p1.verdict == ProbeVerdict.PASS


def test_type3_refuted_by_nesting_promotes_to_type2() -> None:
    a = _bracket_alphabet()
    trace = _trace_from("((BASH))", a, agent="pb.nest")
    contract = _contract(ChomskyClass.TYPE_3)
    report = ProbeHarness(alphabet=a).run(contract=contract, trace=trace)
    assert report.overall_verdict == ProbeVerdict.FAIL
    assert report.recommended_class == ChomskyClass.TYPE_2
    p1 = next(r for r in report.probe_results if r.probe_id == "P1")
    assert p1.verdict == ProbeVerdict.FAIL
    assert p1.refutes_class == ChomskyClass.TYPE_3


def test_type2_dyck_balance_passes() -> None:
    a = _bracket_alphabet()
    trace = _trace_from("([BASH])", a, agent="pb.balanced")
    contract = _contract(ChomskyClass.TYPE_2)
    report = ProbeHarness(alphabet=a).run(contract=contract, trace=trace)
    assert report.overall_verdict == ProbeVerdict.PASS


def test_type2_cross_serial_refuted() -> None:
    a = _bracket_alphabet()
    trace = _trace_from("([)]", a, agent="pb.cross")
    contract = _contract(ChomskyClass.TYPE_2)
    report = ProbeHarness(alphabet=a).run(contract=contract, trace=trace)
    p3 = next(r for r in report.probe_results if r.probe_id == "P3")
    assert p3.verdict == ProbeVerdict.FAIL
    assert p3.refutes_class == ChomskyClass.TYPE_2
    assert report.recommended_class == ChomskyClass.TYPE_1


def test_monitor_certifier_blocks_run() -> None:
    a = _bracket_alphabet()
    trace = _trace_from("BASH", a, agent="pb.mon")
    contract = _contract(ChomskyClass.TYPE_0)
    report_violations = monitor_blacklist_to_violations(
        monitor_id="pb.monitor",
        agent_id="pb.mon",
        run_id="r1",
        hits=[("blacklisted_url", "agent.log:42", "fetched http://forbidden.example")],
    )
    report = ProbeHarness(alphabet=a).run(
        contract=contract, trace=trace, monitor_report=report_violations
    )
    assert report.blocked is True
    assert report.block_reason is not None
    cert = next(r for r in report.probe_results if r.probe_id == "MonitorCertifier")
    assert cert.verdict == ProbeVerdict.FAIL


def test_monitor_certifier_passes_when_clean() -> None:
    a = _bracket_alphabet()
    trace = _trace_from("BASH", a, agent="pb.clean")
    contract = _contract(ChomskyClass.TYPE_0)
    report_violations = monitor_blacklist_to_violations(
        monitor_id="pb.monitor",
        agent_id="pb.clean",
        run_id="r1",
        hits=[],
    )
    report = ProbeHarness(alphabet=a).run(
        contract=contract, trace=trace, monitor_report=report_violations
    )
    assert report.blocked is False


def test_p4_super_linear_refutes_type1() -> None:
    a = _bracket_alphabet()
    # Sizes grow like n^2: 4, 16, 64
    inputs = [2, 4, 8]
    traces = []
    for L in inputs:
        rec = TraceRecorder(agent_id="pb.lin", run_id=f"r{L}", alphabet=a)
        for _ in range(L * L):
            rec.record("bash")
        traces.append(rec.trace())
    contract = _contract(ChomskyClass.TYPE_1)
    harness = ProbeHarness(alphabet=a)
    report = harness.run(
        contract=contract,
        trace=traces[0],
        length_traces=traces,
        length_inputs=inputs,
    )
    p4 = next(r for r in report.probe_results if r.probe_id == "P4")
    assert p4.verdict == ProbeVerdict.FAIL
    assert p4.refutes_class == ChomskyClass.TYPE_1
    assert report.recommended_class == ChomskyClass.TYPE_0


def test_p6_copy_refutes_type2() -> None:
    a = _bracket_alphabet()
    rec = TraceRecorder(agent_id="pb.copy", run_id="r1", alphabet=a)
    for tok in ["round_open", "bash", "square_open", "bash"] * 2:
        rec.record(tok)
    trace = rec.trace()
    contract = _contract(ChomskyClass.TYPE_2)
    report = ProbeHarness(alphabet=a).run(contract=contract, trace=trace)
    p6 = next(r for r in report.probe_results if r.probe_id == "P6")
    assert p6.verdict == ProbeVerdict.FAIL
    assert p6.refutes_class == ChomskyClass.TYPE_2


def test_paperbench_monitor_adapter_scans_log(tmp_path) -> None:
    from chomsky_vv.adapters import PaperBenchMonitorAdapter

    log = tmp_path / "agent.log"
    log.write_text(
        "step 1 ok\n"
        "fetched http://forbidden.example/index\n"
        "step 2 ok\n"
        "leaked SECRET token: abc\n",
        encoding="utf-8",
    )
    adapter = PaperBenchMonitorAdapter(
        monitor_id="pb.monitor",
        agent_id="pb.basicagent",
        run_id="r1",
        rules=[
            ("blacklisted_url", r"forbidden\.example"),
            ("secret_leak", r"SECRET\s+token"),
        ],
    )
    report = adapter.scan_log(log)
    assert len(report.violations) == 2
    assert report.has_blocking_violation is True
    assert {v.rule_id for v in report.violations} == {"blacklisted_url", "secret_leak"}
