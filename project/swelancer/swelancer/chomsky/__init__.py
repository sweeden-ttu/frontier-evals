"""SWE-Lancer binding for the Chomsky V&V contract bus.

Realizes the producer/consumer relationship for swelancer:

  * **Producer 1** — TraceRecorder over the swelancer agent.log discretized
    against :func:`swelancer_default_alphabet` (matches the message-history
    dump emitted by ``solvers/swelancer_agent/solver.py:245``).
  * **Producer 2** — :class:`SwelancerCertifier` — NEW Type-3 non-LLM
    certifier with two pure-function checks: test-bundle isolation
    envelope (Dyck balance over the unzip→user-tool→rm sequence) and a
    python-block CFG validator (AST-only walk rejecting subprocess /
    eval / exec / __import__).
  * **Consumer**   — :class:`chomsky_vv.ProbeHarness` produces
    ``validation_report_v1`` consumed by the lifecycle gate.

The certifier ships in ADVISORY mode (severity=warn) by default so the
gate records evidence without blocking runs while baselines accumulate.
"""

from swelancer.chomsky.alphabet import swelancer_default_alphabet
from swelancer.chomsky.certifier import (
    CertifierMode,
    SwelancerCertifier,
    python_block_cfg_validator,
    verify_test_bundle_isolation,
)
from swelancer.chomsky.contracts import (
    SwelancerAgentId,
    classification_for,
    default_classifications,
)
from swelancer.chomsky.gate import GateMode, GateResult, run_lifecycle_gate

__all__ = [
    "CertifierMode",
    "GateMode",
    "GateResult",
    "SwelancerAgentId",
    "SwelancerCertifier",
    "classification_for",
    "default_classifications",
    "python_block_cfg_validator",
    "run_lifecycle_gate",
    "swelancer_default_alphabet",
    "verify_test_bundle_isolation",
]
