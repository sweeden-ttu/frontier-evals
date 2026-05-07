"""SWE-Lancer Σ-alphabet for the chomsky_vv trace recorder.

Patterns are grounded in actual ``ctx_logger.info(...)`` and ``messages.append``
sites verified in:

  * solvers/swelancer_agent/solver.py:110  — Trimming message…
  * solvers/swelancer_agent/solver.py:217  — Starting computer…
  * solvers/swelancer_agent/solver.py:245  — message history dump (full
    ``messages`` list with role/content shape)
  * solvers/swelancer_agent/solver.py:257  — User tool call detected
  * solvers/swelancer_agent/solver.py:278  — No user tool call detected
  * solvers/swelancer_agent/solver.py:283  — python_blocks regex extractor
  * solvers/swelancer_agent/solver.py:300  — python -c dispatch
  * solvers/swelancer_agent/solver.py:310  — Agent code timed out

The role-tagged regexes ``swe_role_*`` match the str-repr of the
``messages`` list as it is logged at line 246 (``f"...{messages}"``); the
default Python repr of ``{"role": "user", ...}`` uses single quotes, so
both quote styles are accepted.
"""

from __future__ import annotations

from chomsky_vv import Alphabet, TokenSpec


def swelancer_default_alphabet() -> Alphabet:
    return Alphabet(
        tokens=[
            TokenSpec(name="swe_starting_computer", pattern=r"Starting computer\.\.\."),
            TokenSpec(name="swe_trim_message", pattern=r"Trimming message\.\.\."),
            TokenSpec(name="swe_message_history", pattern=r"Message history on turn \d+"),
            TokenSpec(name="swe_user_tool_detected", pattern=r"User tool call detected"),
            TokenSpec(
                name="swe_user_tool_not_detected", pattern=r"No user tool call detected"
            ),
            TokenSpec(name="swe_agent_timeout", pattern=r"Agent code timed out"),
            TokenSpec(
                name="swe_role_user", pattern=r"['\"]role['\"]\s*:\s*['\"]user['\"]"
            ),
            TokenSpec(
                name="swe_role_assistant",
                pattern=r"['\"]role['\"]\s*:\s*['\"]assistant['\"]",
            ),
            TokenSpec(
                name="swe_role_tool", pattern=r"['\"]role['\"]\s*:\s*['\"]tool['\"]"
            ),
            TokenSpec(name="swe_python_block_open", pattern=r"```python", push=True),
            TokenSpec(
                name="swe_python_block_close",
                pattern=r"```(?!python)",
                pop=True,
                pairs_with="swe_python_block_open",
            ),
            TokenSpec(name="swe_user_tool_open", pattern=r"<user-tool>"),
            TokenSpec(name="swe_user_tool_close", pattern=r"</user-tool>"),
        ]
    )
