"""Pydantic schemas for the Chomsky V&V contract bus.

All schemas carry an explicit ``schema`` field so producers and consumers can
identify the contract version they are exchanging without out-of-band metadata.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChomskyClass(str, Enum):
    TYPE_0 = "Type-0"
    TYPE_1 = "Type-1"
    TYPE_2 = "Type-2"
    TYPE_3 = "Type-3"


# Most-permissive (Type-0) ranks higher than most-restrictive (Type-3); a
# refutation against a class forces a strict promotion toward Type-0.
_RANK = {
    ChomskyClass.TYPE_3: 0,
    ChomskyClass.TYPE_2: 1,
    ChomskyClass.TYPE_1: 2,
    ChomskyClass.TYPE_0: 3,
}


def class_rank(cls: ChomskyClass) -> int:
    return _RANK[cls]


def promote(refuted: ChomskyClass) -> ChomskyClass:
    """Return the next-strictly-more-permissive class than ``refuted``."""
    idx = _RANK[refuted] + 1
    if idx >= len(_RANK):
        return ChomskyClass.TYPE_0
    for cls, rank in _RANK.items():
        if rank == idx:
            return cls
    return ChomskyClass.TYPE_0


class StructuralWitness(BaseModel):
    witness_kind: str
    source_ref: str
    confidence: float = Field(ge=0.0, le=1.0)


class MemoryHypothesis(BaseModel):
    workspace_class: Literal["bounded", "linear", "unbounded"]
    external_store: Literal["none", "filesystem", "network", "unknown"]


class VVObligationBudget(BaseModel):
    verification_time_budget_seconds: int = Field(ge=0)
    test_case_count: int = Field(ge=0)
    judge_call_budget: int = Field(ge=0)


class ChomskyClassification(BaseModel):
    """``chomsky_classification_v1`` — producer contract."""

    model_config = ConfigDict(populate_by_name=True)

    schema_name: Literal["chomsky_classification_v1"] = Field(
        default="chomsky_classification_v1", alias="schema"
    )
    agent_id: str
    source_paths: list[str] = Field(default_factory=list)
    sigma_trace_alphabet_encoding: list[str] = Field(default_factory=list)
    predicted_chomsky_class: ChomskyClass
    structural_witnesses: list[StructuralWitness] = Field(default_factory=list)
    memory_hypothesis: MemoryHypothesis
    probe_plan_ref: str = "P0_type0_full"
    vv_obligation_budget: VVObligationBudget


class TraceToken(BaseModel):
    token: str
    ts_seq: int = Field(ge=0)
    payload_hash: str | None = None
    source_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceRecord(BaseModel):
    """``sigma_trace_v1`` — output of the TraceRecorder; consumed by probes."""

    model_config = ConfigDict(populate_by_name=True)

    schema_name: Literal["sigma_trace_v1"] = Field(default="sigma_trace_v1", alias="schema")
    agent_id: str
    run_id: str
    alphabet_names: list[str] = Field(default_factory=list)
    tokens: list[TraceToken] = Field(default_factory=list)


class MonitorViolation(BaseModel):
    rule_id: str
    severity: Literal["info", "warn", "error"] = "error"
    source_ref: str | None = None
    excerpt: str = ""


class MonitorViolationReport(BaseModel):
    """``monitor_violation_v1`` — output of the PaperBench Monitor adapter.

    Treated as an authoritative non-LLM certifier verdict. A non-empty list
    of error-severity violations is sufficient to block the run regardless
    of declared Chomsky class.
    """

    model_config = ConfigDict(populate_by_name=True)

    schema_name: Literal["monitor_violation_v1"] = Field(
        default="monitor_violation_v1", alias="schema"
    )
    agent_id: str
    run_id: str
    monitor_id: str
    violations: list[MonitorViolation] = Field(default_factory=list)

    @property
    def has_blocking_violation(self) -> bool:
        return any(v.severity == "error" for v in self.violations)


class ProbeVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    SKIPPED = "skipped"


class ProbeResult(BaseModel):
    probe_id: str
    verdict: ProbeVerdict
    refutes_class: ChomskyClass | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class ValidationReport(BaseModel):
    """``validation_report_v1`` — consumer output of the probe harness."""

    model_config = ConfigDict(populate_by_name=True)

    schema_name: Literal["validation_report_v1"] = Field(
        default="validation_report_v1", alias="schema"
    )
    agent_id: str
    run_id: str
    declared_class: ChomskyClass
    probe_results: list[ProbeResult] = Field(default_factory=list)
    overall_verdict: ProbeVerdict
    recommended_class: ChomskyClass | None = None
    blocked: bool = False
    block_reason: str | None = None
