"""EVMBench Σ-alphabet for the chomsky_vv trace recorder.

Patterns are grounded in actual ``ctx_logger.info(...)`` emission sites
verified in:

  * project/evmbench/evmbench/nano/solver.py:435   — detect iteration start
  * project/evmbench/evmbench/nano/solver.py:505   — detect iteration end
  * project/evmbench/evmbench/nano/solver.py:474   — audit download failure
  * project/evmbench/evmbench/ploit/veto.py:257    — Veto proxy started
  * project/evmbench/evmbench/ploit/veto.py:298    — Veto proxy stopped
  * project/evmbench/evmbench/agents/run.py:42-93  — agent lifecycle
  * project/evmbench/evmbench/nano/grade/exploit.py / patch.py — grader output

Veto's own RPC allow/deny stream is captured to a separate file
(``LOGS_DIR/veto.log``) and consumed via :mod:`veto_bridge`; this
alphabet covers ``agent.log`` only.
"""

from __future__ import annotations

from chomsky_vv import Alphabet, TokenSpec


def evmbench_default_alphabet() -> Alphabet:
    return Alphabet(
        tokens=[
            TokenSpec(name="evm_iter_start", pattern=r"Starting detect iteration \d+/\d+", push=True),
            TokenSpec(
                name="evm_iter_complete",
                pattern=r"Completed detect iteration \d+/\d+",
                pop=True,
                pairs_with="evm_iter_start",
            ),
            TokenSpec(name="evm_iter_failed", pattern=r"Failed to download audit report"),
            TokenSpec(name="evm_veto_started", pattern=r"Started Veto proxy\."),
            TokenSpec(name="evm_veto_stopped", pattern=r"Stopped Veto proxy\."),
            TokenSpec(name="evm_agent_finished", pattern=r"Agent finished successfully\."),
            TokenSpec(name="evm_agent_failed", pattern=r"Run failed with error"),
            TokenSpec(name="evm_agent_waiting", pattern=r"Waiting for agent to finish"),
            TokenSpec(name="evm_agent_complete", pattern=r"Run completed in [\d\.]+ seconds"),
            TokenSpec(name="evm_alcatraz_config", pattern=r"alcatraz_config:"),
            TokenSpec(name="evm_starting_computer", pattern=r"Starting computer"),
            TokenSpec(name="evm_grade_pass", pattern=r"\bverdict=pass\b"),
            TokenSpec(name="evm_grade_fail", pattern=r"\bverdict=fail\b"),
        ]
    )
