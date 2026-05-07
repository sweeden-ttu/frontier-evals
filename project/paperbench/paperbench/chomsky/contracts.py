"""Default ``chomsky_classification_v1`` contracts for known PaperBench agents.

Reflects the inventory produced by the chomsky-agent classification sweep.
Source-path references are relative to the repository root so contracts
can be persisted and replayed without absolute-path resolution.
"""

from __future__ import annotations

from typing import Literal

from chomsky_vv import (
    ChomskyClass,
    ChomskyClassification,
    MemoryHypothesis,
    StructuralWitness,
    VVObligationBudget,
)

PaperBenchAgentId = Literal[
    "pb.basicagent",
    "pb.iterative_agent",
    "pb.dummy",
    "pb.direct_submission",
    "pb.human",
    "pb.simple_judge",
    "pb.dummy_judge",
    "pb.random_judge",
    "pb.monitor",
]


def _basicagent() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.basicagent",
        source_paths=[
            "project/paperbench/paperbench/solvers/basicagent/solver.py",
            "project/paperbench/paperbench/solvers/basicagent/tools/basic.py",
        ],
        sigma_trace_alphabet_encoding=[
            "bash",
            "python",
            "read_file_chunk",
            "search_file",
            "submit",
            "web_search",
            "reminder",
            "prune",
            "upload",
            "retry",
        ],
        predicted_chomsky_class=ChomskyClass.TYPE_0,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="subprocess_spawn",
                source_ref="project/paperbench/paperbench/solvers/basicagent/tools/basic.py:42",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="subprocess_spawn",
                source_ref="project/paperbench/paperbench/solvers/basicagent/tools/basic.py:68",
                confidence=1.0,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="unbounded", external_store="filesystem"),
        probe_plan_ref="P0_type0_full",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=600,
            test_case_count=200,
            judge_call_budget=50,
        ),
    )


def _iterative_agent() -> ChomskyClassification:
    c = _basicagent().model_copy(deep=True)
    c.agent_id = "pb.iterative_agent"
    c.sigma_trace_alphabet_encoding = ["bash", "read_file_chunk", "submit", "reminder", "prune", "retry"]
    return c


def _simple_judge() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.simple_judge",
        source_paths=[
            "project/paperbench/paperbench/judge/simple.py",
            "project/paperbench/paperbench/judge/base.py",
        ],
        sigma_trace_alphabet_encoding=[
            "judge_push",
            "judge_pop",
            "submit",
            "prune",
            "retry",
        ],
        predicted_chomsky_class=ChomskyClass.TYPE_2,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="recursion_site",
                source_ref="project/paperbench/paperbench/judge/base.py:121",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/paperbench/paperbench/judge/base.py:137",
                confidence=0.95,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="linear", external_store="filesystem"),
        probe_plan_ref="P2_balanced_depth",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=300,
            test_case_count=100,
            judge_call_budget=200,
        ),
    )


def _dummy() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.dummy",
        source_paths=["project/paperbench/paperbench/solvers/dummy/solver.py"],
        sigma_trace_alphabet_encoding=["bash"],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="none"),
        probe_plan_ref="P1_pumping_lemma",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=60, test_case_count=50, judge_call_budget=0
        ),
    )


def _direct_submission() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.direct_submission",
        source_paths=["project/paperbench/paperbench/solvers/direct_submission/solver.py"],
        sigma_trace_alphabet_encoding=["submit"],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="filesystem"),
        probe_plan_ref="P1_pumping_lemma",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=60, test_case_count=40, judge_call_budget=0
        ),
    )


def _human() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.human",
        source_paths=["project/paperbench/paperbench/solvers/human/start.sh"],
        sigma_trace_alphabet_encoding=[],
        predicted_chomsky_class=ChomskyClass.TYPE_0,
        memory_hypothesis=MemoryHypothesis(workspace_class="unbounded", external_store="unknown"),
        probe_plan_ref="P0_type0_full",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=0, test_case_count=0, judge_call_budget=0
        ),
    )


def _dummy_judge() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.dummy_judge",
        source_paths=["project/paperbench/paperbench/judge/dummyrandom.py"],
        sigma_trace_alphabet_encoding=[],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="none"),
        probe_plan_ref="P1_pumping_lemma",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=10, test_case_count=10, judge_call_budget=0
        ),
    )


def _random_judge() -> ChomskyClassification:
    c = _dummy_judge().model_copy(deep=True)
    c.agent_id = "pb.random_judge"
    return c


def _monitor() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="pb.monitor",
        source_paths=["project/paperbench/paperbench/monitor/monitor.py"],
        sigma_trace_alphabet_encoding=[],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        memory_hypothesis=MemoryHypothesis(workspace_class="linear", external_store="none"),
        probe_plan_ref="P1_pumping_lemma",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=60, test_case_count=200, judge_call_budget=0
        ),
    )


_REGISTRY: dict[str, ChomskyClassification] = {
    "pb.basicagent": _basicagent(),
    "pb.iterative_agent": _iterative_agent(),
    "pb.dummy": _dummy(),
    "pb.direct_submission": _direct_submission(),
    "pb.human": _human(),
    "pb.simple_judge": _simple_judge(),
    "pb.dummy_judge": _dummy_judge(),
    "pb.random_judge": _random_judge(),
    "pb.monitor": _monitor(),
}


def classification_for(agent_id: PaperBenchAgentId | str) -> ChomskyClassification:
    if agent_id not in _REGISTRY:
        raise KeyError(
            f"unknown paperbench agent_id {agent_id!r}; "
            f"known: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[agent_id].model_copy(deep=True)


def default_classifications() -> dict[str, ChomskyClassification]:
    return {k: v.model_copy(deep=True) for k, v in _REGISTRY.items()}
