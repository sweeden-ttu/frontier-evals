"""Canonical banned-token policy.

A single ``BannedTokenPolicy`` drives all four enforcement layers (V&V
probe, grader penalty, logits processor, RL reward) so the punishment
intensity is one config edit away. Each ``BannedToken`` carries a
severity, a match-kind (``word``, ``literal``, or ``domain``), and an
optional weight. The policy also stores the four numeric punishment
knobs documented in the plan.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

MatchKind = Literal["word", "literal", "domain"]
Severity = Literal["info", "warn", "error"]


class BannedToken(BaseModel):
    """A single banned token with its enforcement metadata."""

    model_config = ConfigDict(populate_by_name=True)

    token: str
    severity: Severity = "error"
    match_kind: MatchKind = "word"
    weight: float = 1.0


class BannedTokenPolicy(BaseModel):
    """Canonical registry consumed by every enforcement layer.

    ``tokens`` is the source of truth. ``allowlist_identifiers`` is
    consulted *after* a candidate hit so projects can carve out specific
    legitimate uses (e.g. the ``dummy`` agent id) without dropping the
    token from the registry. ``weights`` overrides per-token weights
    without rewriting the ``tokens`` list.
    """

    model_config = ConfigDict(populate_by_name=True)

    tokens: list[BannedToken] = Field(default_factory=list)
    allowlist_identifiers: list[str] = Field(default_factory=list)
    per_extension_overrides: dict[str, list[str]] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)

    grader_score_scale: float = 10.0
    logits_soft_penalty: float = -50.0
    logits_hard_mode: bool = False
    rl_lambda: float = 1.0

    def weight_for(self, token: str) -> float:
        """Return the effective weight for ``token`` (override > token > 1.0)."""
        if token in self.weights:
            return float(self.weights[token])
        for bt in self.tokens:
            if bt.token == token:
                return float(bt.weight)
        return 1.0

    def severity_for(self, token: str) -> Severity:
        for bt in self.tokens:
            if bt.token == token:
                return bt.severity
        return "error"

    def is_allowlisted(self, identifier: str) -> bool:
        return identifier in set(self.allowlist_identifiers)

    def banned_token(self, name: str) -> BannedToken | None:
        """Return the BannedToken matching ``name`` (case-insensitive), if any."""
        lower = name.lower()
        for bt in self.tokens:
            if bt.token == name or bt.token.lower() == lower:
                return bt
        return None


_DEFAULT_POLICY_PATH = Path(__file__).parent / "policy.yaml"


def load_policy(path: str | Path) -> BannedTokenPolicy:
    """Load a ``BannedTokenPolicy`` from a YAML file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return BannedTokenPolicy.model_validate(data)


def default_policy() -> BannedTokenPolicy:
    """Return the canonical default policy bundled with the package."""
    return load_policy(_DEFAULT_POLICY_PATH)
