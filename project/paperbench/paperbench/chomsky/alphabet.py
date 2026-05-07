"""PaperBench Σ-alphabet for the chomsky_vv trace recorder.

Σ-tokens cover the BasicAgent / IterativeAgent tool surface plus the
push/pop boundaries of the SimpleJudge rubric recursion. Patterns are
matched against ``agent.log`` lines as written by
:class:`paperbench.solvers.basicagent.completer.LoggableMessages`.

The push/pop pair (``judge_push`` ↔ ``judge_pop``) makes the Dyck-balance
probe (P2) and the cross-serial probe (P3) directly applicable to judge
transcripts that are interleaved with rollout logs.
"""

from __future__ import annotations

from chomsky_vv import Alphabet, TokenSpec


def paperbench_default_alphabet() -> Alphabet:
    return Alphabet(
        tokens=[
            TokenSpec(name="bash", pattern=r"BashTool\.execute"),
            TokenSpec(name="python", pattern=r"PythonTool\.execute"),
            TokenSpec(name="read_file_chunk", pattern=r"ReadFileChunk"),
            TokenSpec(name="search_file", pattern=r"SearchFile"),
            TokenSpec(name="submit", pattern=r"SubmitTool"),
            TokenSpec(name="web_search", pattern=r"WebSearchTool"),
            TokenSpec(name="reminder", pattern=r"\[reminder\]"),
            TokenSpec(name="prune", pattern=r"\[prune\]|LengthFinishReasonError"),
            TokenSpec(name="upload", pattern=r"\[upload\]|periodic upload"),
            TokenSpec(name="retry", pattern=r"\[retry\]|RateLimitError"),
            TokenSpec(name="judge_push", pattern=r"grade\(.+depth=\d+", push=True),
            TokenSpec(
                name="judge_pop",
                pattern=r"grade\.return\b",
                pop=True,
                pairs_with="judge_push",
            ),
        ]
    )
