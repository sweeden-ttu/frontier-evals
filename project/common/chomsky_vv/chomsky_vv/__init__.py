"""Shared Chomsky-hierarchy V&V framework: trace recorder + probe harness."""

from chomsky_vv.alphabet import Alphabet, TokenSpec
from chomsky_vv.banned import (
    BannedToken,
    BannedTokenCertifier,
    BannedTokenMatcher,
    BannedTokenPolicy,
    Hit,
    apply_to_score,
    banned_reward_penalty,
    compute_penalty,
    default_policy,
    load_policy,
    penalty_to_score_delta,
)
from chomsky_vv.harness import ProbeHarness
from chomsky_vv.recorder import TraceRecorder
from chomsky_vv.schemas import (
    ChomskyClass,
    ChomskyClassification,
    MemoryHypothesis,
    MonitorViolation,
    MonitorViolationReport,
    ProbeResult,
    ProbeVerdict,
    StructuralWitness,
    TraceRecord,
    TraceToken,
    ValidationReport,
    VVObligationBudget,
)

__all__ = [
    "Alphabet",
    "BannedToken",
    "BannedTokenCertifier",
    "BannedTokenMatcher",
    "BannedTokenPolicy",
    "ChomskyClass",
    "ChomskyClassification",
    "Hit",
    "MemoryHypothesis",
    "MonitorViolation",
    "MonitorViolationReport",
    "ProbeHarness",
    "ProbeResult",
    "ProbeVerdict",
    "StructuralWitness",
    "TokenSpec",
    "TraceRecord",
    "TraceRecorder",
    "TraceToken",
    "ValidationReport",
    "VVObligationBudget",
    "apply_to_score",
    "banned_reward_penalty",
    "compute_penalty",
    "default_policy",
    "load_policy",
    "penalty_to_score_delta",
]
