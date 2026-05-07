"""PaperBench binding for the Chomsky V&V contract bus.

Wires the existing PaperBench :class:`~paperbench.monitor.monitor.Monitor`
(non-LLM Type-3 certifier) and the canonical paperbench Σ-alphabet onto the
``chomsky_vv`` producer/consumer pipeline so the rollout→grading transition
can be gated on a ``validation_report_v1`` verdict.

Producer/consumer wiring (per ``frontier.yaml``):

  TraceRecorder       --[sigma_trace_v1]-->        ProbeHarness
  PaperBench Monitor  --[monitor_violation_v1]-->  ProbeHarness
                                                    |
                                                    v
                                             validation_report_v1
                                                    |
                                                    v
                                       run_judge gate (block / warn)
"""

from paperbench.chomsky.alphabet import paperbench_default_alphabet
from paperbench.chomsky.contracts import (
    PaperBenchAgentId,
    classification_for,
    default_classifications,
)
from paperbench.chomsky.gate import (
    GateMode,
    GateResult,
    find_agent_log,
    run_rollout_to_grading_gate,
)
from paperbench.chomsky.monitor_bridge import monitor_result_to_violation_report

__all__ = [
    "GateMode",
    "GateResult",
    "PaperBenchAgentId",
    "classification_for",
    "default_classifications",
    "find_agent_log",
    "monitor_result_to_violation_report",
    "paperbench_default_alphabet",
    "run_rollout_to_grading_gate",
]
