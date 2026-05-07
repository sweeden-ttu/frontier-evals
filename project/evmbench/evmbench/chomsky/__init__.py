"""EVMBench binding for the Chomsky V&V contract bus.

Wires the Veto Rust sidecar (existing Type-3 RPC certifier) and a
benchmark-specific Σ-alphabet onto the ``chomsky_vv`` producer/consumer
pipeline. EVMBench's lifecycle is detect / patch / exploit; the gate
discharges the certifier verdict before grading proceeds.
"""

from evmbench.chomsky.alphabet import evmbench_default_alphabet
from evmbench.chomsky.contracts import (
    EvmBenchAgentId,
    classification_for,
    default_classifications,
)
from evmbench.chomsky.gate import GateMode, GateResult, run_lifecycle_gate
from evmbench.chomsky.veto_bridge import scan_veto_log

__all__ = [
    "GateMode",
    "GateResult",
    "EvmBenchAgentId",
    "classification_for",
    "default_classifications",
    "evmbench_default_alphabet",
    "run_lifecycle_gate",
    "scan_veto_log",
]
