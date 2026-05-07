"""Default ``chomsky_classification_v1`` contracts for swelancer agents.

``swe.simple_agent`` is a Type-1 envelope (max_turns=40, MODEL_TO_CTX_LIMIT
trim_messages workspace bound) that EMBEDS a Type-0 island via the
``python -c {shlex.quote(code)}`` dispatch and the ``<user-tool>`` shell
sequence. The conservative envelope is Type-0 for any rollout that
contains a ``swe_user_tool_open`` or any ``swe_python_block_open`` token
whose payload fails the python_block_cfg_validator. Until Gap 4's AST
classifier runs, the manual default is Type-0.
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

SwelancerAgentId = Literal["swe.simple_agent", "swe.dummy"]


def _simple_agent() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="swe.simple_agent",
        source_paths=[
            "project/swelancer/swelancer/solvers/swelancer_agent/solver.py",
            "project/swelancer/swelancer/eval.py",
        ],
        sigma_trace_alphabet_encoding=[
            "swe_starting_computer",
            "swe_trim_message",
            "swe_message_history",
            "swe_user_tool_detected",
            "swe_user_tool_not_detected",
            "swe_agent_timeout",
            "swe_python_block_open",
            "swe_python_block_close",
            "swe_user_tool_open",
            "swe_user_tool_close",
        ],
        predicted_chomsky_class=ChomskyClass.TYPE_0,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/swelancer/swelancer/solvers/swelancer_agent/solver.py:230",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/swelancer/swelancer/solvers/swelancer_agent/solver.py:108",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="subprocess_spawn",
                source_ref="project/swelancer/swelancer/solvers/swelancer_agent/solver.py:300",
                confidence=1.0,
            ),
            StructuralWitness(
                witness_kind="subprocess_spawn",
                source_ref="project/swelancer/swelancer/solvers/swelancer_agent/solver.py:262",
                confidence=1.0,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="linear", external_store="filesystem"),
        probe_plan_ref="P0_type0_full",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=600,
            test_case_count=150,
            judge_call_budget=0,
        ),
    )


def _dummy() -> ChomskyClassification:
    return ChomskyClassification(
        agent_id="swe.dummy",
        source_paths=["project/swelancer/swelancer/solvers/dummy/solver.py"],
        sigma_trace_alphabet_encoding=["swe_user_tool_open", "swe_user_tool_close"],
        predicted_chomsky_class=ChomskyClass.TYPE_3,
        structural_witnesses=[
            StructuralWitness(
                witness_kind="bounded_loop",
                source_ref="project/swelancer/swelancer/solvers/dummy/solver.py:114",
                confidence=1.0,
            ),
        ],
        memory_hypothesis=MemoryHypothesis(workspace_class="bounded", external_store="filesystem"),
        probe_plan_ref="P1_pumping_lemma",
        vv_obligation_budget=VVObligationBudget(
            verification_time_budget_seconds=60,
            test_case_count=40,
            judge_call_budget=0,
        ),
    )


_REGISTRY: dict[str, ChomskyClassification] = {
    "swe.simple_agent": _simple_agent(),
    "swe.dummy": _dummy(),
}


def classification_for(agent_id: SwelancerAgentId | str) -> ChomskyClassification:
    if agent_id not in _REGISTRY:
        raise KeyError(
            f"unknown swelancer agent_id {agent_id!r}; known: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[agent_id].model_copy(deep=True)


def default_classifications() -> dict[str, ChomskyClassification]:
    return {k: v.model_copy(deep=True) for k, v in _REGISTRY.items()}
