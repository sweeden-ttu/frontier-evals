from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

ChomskyClass = Literal["Type-3", "Type-2", "Type-1", "Type-0"]


@dataclass
class ChomskyClassificationV1:
    schema: str = "chomsky_classification_v1"
    agent_id: str = ""
    source_paths: list[str] = field(default_factory=list)
    sigma_trace_alphabet_encoding: list[str] = field(default_factory=list)
    predicted_chomsky_class: ChomskyClass = "Type-3"
    structural_witnesses: list[str] = field(default_factory=list)
    memory_hypothesis: str = ""
    probe_plan_ref: str | None = None
    vv_obligation_budget: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChomskyClassificationV1:
        return cls(
            schema=data.get("schema", "chomsky_classification_v1"),
            agent_id=data["agent_id"],
            source_paths=list(data.get("source_paths", [])),
            sigma_trace_alphabet_encoding=list(data.get("sigma_trace_alphabet_encoding", [])),
            predicted_chomsky_class=data["predicted_chomsky_class"],
            structural_witnesses=list(data.get("structural_witnesses", [])),
            memory_hypothesis=data.get("memory_hypothesis", ""),
            probe_plan_ref=data.get("probe_plan_ref"),
            vv_obligation_budget=int(data.get("vv_obligation_budget", 0)),
        )


@dataclass
class CheckResult:
    name: str
    status: Literal["PASS", "FAIL"]
    evidence: str


@dataclass
class VerificationReportV1:
    schema: str = "verification_report_v1"
    agent_id: str = ""
    predicted_class: ChomskyClass = "Type-3"
    demoted_to: ChomskyClass | None = None
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.status == "PASS" for c in self.checks)

    def to_json(self) -> str:
        payload = asdict(self)
        return json.dumps(payload, indent=2)


@dataclass
class ValidationReport:
    path: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    column_count: int = 0
    row_count: int = 0
    agent_columns: list[str] = field(default_factory=list)


def new_id() -> str:
    return str(uuid.uuid4())


def contracts_dir() -> Path:
    return Path(__file__).resolve().parent / "contracts"
