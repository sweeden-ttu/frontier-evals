"""Default ``chomsky_classification_v1`` contracts for known EVMBench agents.

Reflects the inventory from the prior Chomsky V&V sweep. Source paths are
relative to repository root. These will be replaced by AST-derived
classifications once Gap 4 lands; for now they are the calibration baseline.
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

EvmBenchAgentId = Literal[
    "evm.solver",
    "evm.external_agents.claude",
    "evm.external_agents.codex",
    "evm.external_agents.gemini",
    "evm.external_agents.opencode",
    "evm.veto",
    "evm.detect_grader",
    "evm.patch_grader",
    "evm.exploit_grader",
]


def _solver() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="evm.solver",
        source_paths=[
            "project/evmbench/evmbench/nano/solver.py",
            "project/evmbench/evmbench/agents/agent.py",
            "project/evmbench/evmbench/agents/run.py",
        ],
        sigma_trace_alphabet_encoding=[
            "evm_iter_start",
            "evm_iter_complete",
            "evm_iter_failed",
            "evm_agent_finished",
            "evm_agent_failed",
            "evm_starting_computer",
        ],
        predicted_chomsky_class=ChomskyClass.TYPE_0,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="subprocess_spawn",
                source_ref="project/evmbench/evmbench/nano/solver.py:303",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/evmbench/evmbench/nano/solver.py:434",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="schema_validator",
                source_ref="project/evmbench/evmbench/agents/agent.py:62",
                confidence=0.9,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="unbounded", external_store="network"),
        probe_plan_ref="P0_type0_full",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=900,
            test_case_count=100,
            judge_call_budget=0,
        ),
    )


def _external_agent(name: str) -> ChomskyClassification:
    return ChomskyClassification(
        agent_id=f"evm.external_agents.{name}",
        source_paths=[
            f"project/evmbench/evmbench/agents/{name}/start.sh",
            f"project/evmbench/evmbench/agents/{name}/config.yaml",
        ],
        sigma_trace_alphabet_encoding=[],
        predicted_chomsky_class=ChomskyClass.TYPE_0,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="subprocess_spawn",
                source_ref=f"project/evmbench/evmbench/agents/{name}/start.sh:1",
                confidence=1.0,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="unbounded", external_store="network"),
        probe_plan_ref="P0_type0_full",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=1200,
            test_case_count=100,
            judge_call_budget=0,
        ),
    )


def _veto() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="evm.veto",
        source_paths=[
            "project/evmbench/evmbench/ploit/veto.py",
            "project/evmbench/veto/Cargo.toml",
        ],
        sigma_trace_alphabet_encoding=["evm_veto_started", "evm_veto_stopped"],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="schema_validator",
                source_ref="project/evmbench/evmbench/ploit/veto.py:30",
                confidence=1.0,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="none"),
        probe_plan_ref="P1_pumping_lemma",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=120,
            test_case_count=300,
            judge_call_budget=0,
        ),
    )


def _detect_grader() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="evm.detect_grader",
        source_paths=[
            "project/evmbench/evmbench/nano/grade/detect.py",
            "project/evmbench/evmbench/nano/grade/base.py",
        ],
        sigma_trace_alphabet_encoding=["evm_grade_pass", "evm_grade_fail"],
        predicted_chomsky_class=ChomskyClass.TYPE_1,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/evmbench/evmbench/nano/grade/detect.py:40",
                confidence=0.9,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="linear", external_store="filesystem"),
        probe_plan_ref="P4_workspace_linearity",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=120,
            test_case_count=80,
            judge_call_budget=0,
        ),
    )


def _patch_grader() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="evm.patch_grader",
        source_paths=[
            "project/evmbench/evmbench/nano/grade/patch.py",
            "project/evmbench/evmbench/nano/grade/base.py",
        ],
        sigma_trace_alphabet_encoding=["evm_grade_pass", "evm_grade_fail"],
        predicted_chomsky_class=ChomskyClass.TYPE_2,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="schema_validator",
                source_ref="project/evmbench/evmbench/nano/grade/patch.py:43",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="recursion_site",
                source_ref="project/evmbench/evmbench/nano/grade/patch.py:18",
                confidence=0.7,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="linear", external_store="filesystem"),
        probe_plan_ref="P2_balanced_depth",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=300,
            test_case_count=100,
            judge_call_budget=0,
        ),
    )


def _exploit_grader() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="evm.exploit_grader",
        source_paths=[
            "project/evmbench/evmbench/nano/grade/exploit.py",
            "project/evmbench/evmbench/nano/grade/base.py",
        ],
        sigma_trace_alphabet_encoding=["evm_grade_pass", "evm_grade_fail"],
        predicted_chomsky_class=ChomskyClass.TYPE_1,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/evmbench/evmbench/nano/grade/exploit.py:43",
                confidence=0.9,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="linear", external_store="network"),
        probe_plan_ref="P4_workspace_linearity",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=600,
            test_case_count=80,
            judge_call_budget=0,
        ),
    )


_REGISTRY: dict[str, ChomskyClassification] = {
    "evm.solver": _solver(),
    "evm.external_agents.claude": _external_agent("claude"),
    "evm.external_agents.codex": _external_agent("codex"),
    "evm.external_agents.gemini": _external_agent("gemini"),
    "evm.external_agents.opencode": _external_agent("opencode"),
    "evm.veto": _veto(),
    "evm.detect_grader": _detect_grader(),
    "evm.patch_grader": _patch_grader(),
    "evm.exploit_grader": _exploit_grader(),
}


def classification_for(agent_id: EvmBenchAgentId | str) -> ChomskyClassification:
    if agent_id not in _REGISTRY:
        raise KeyError(
            f"unknown evmbench agent_id {agent_id!r}; known: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[agent_id].model_copy(deep=True)


def default_classifications() -> dict[str, ChomskyClassification]:
    return {k: v.model_copy(deep=True) for k, v in _REGISTRY.items()}
