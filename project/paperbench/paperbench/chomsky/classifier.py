from __future__ import annotations

import ast
import re
from pathlib import Path

from paperbench.chomsky.schema import ChomskyClassificationV1, ChomskyClass
from paperbench.chomsky.trace_csv import CLI_PATTERN, collect_alphabet, validate_trace_language_csv

TYPE0_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\brequests\b"),
    re.compile(r"\bos\.system\b"),
    re.compile(r"\bPopen\b"),
    re.compile(r"\bhttpx\b"),
    re.compile(r"\bopen\s*\("),
)
TYPE2_TOKENS = frozenset({"add_task", "add_dep", "topological_order", "dispatch"})
TYPE3_TOKENS = frozenset({"pin_seed", "dispatch"})


def _max_class(a: ChomskyClass, b: ChomskyClass) -> ChomskyClass:
    order = {"Type-3": 0, "Type-2": 1, "Type-1": 2, "Type-0": 3}
    return a if order[a] >= order[b] else b


def classify_trace_csv(path: Path | str, *, agent_id: str | None = None) -> ChomskyClassificationV1:
    path = Path(path)
    agent_id = agent_id or path.parent.name or path.stem
    report = validate_trace_language_csv(path, require_canonical_header=False)
    alphabet = collect_alphabet(path)
    alphabet_set = set(alphabet)

    predicted: ChomskyClass = "Type-3"
    witnesses: list[str] = []
    memory = "finite register file (swim-lane dispatch over bounded agent modes)"

    if any(CLI_PATTERN.search(tok) for tok in alphabet):
        predicted = "Type-0"
        witnesses.append("CLI/subprocess tokens in trace alphabet (kaggle/sbatch/uv/etc.)")
        memory = "unbounded external store envelope (filesystem, Slurm, Kaggle API)"

    if TYPE2_TOKENS & alphabet_set:
        predicted = _max_class(predicted, "Type-2")
        witnesses.append("dependency-graph tokens: add_task/add_dep/topological_order/dispatch")
        if predicted != "Type-0":
            memory = "stack-structured subgoal memory (pushdown-style orchestration)"

    if len(alphabet) > 40 and predicted not in ("Type-0",):
        predicted = _max_class(predicted, "Type-1")
        witnesses.append(f"large trace alphabet ({len(alphabet)} tokens) suggests linear transcript growth")

    if TYPE3_TOKENS <= alphabet_set and predicted == "Type-3":
        witnesses.append("finite control via pin_seed + dispatch governance rows")

    return ChomskyClassificationV1(
        agent_id=agent_id,
        source_paths=[str(path.resolve())],
        sigma_trace_alphabet_encoding=alphabet,
        predicted_chomsky_class=predicted,
        structural_witnesses=witnesses,
        memory_hypothesis=memory,
        vv_obligation_budget=max(4, len(witnesses) * 2),
    )


def classify_solver_module(module_path: Path | str) -> ChomskyClassificationV1:
    """Static field analysis on a Python solver module."""
    path = Path(module_path)
    source = path.read_text(encoding="utf-8")
    agent_id = path.stem

    predicted: ChomskyClass = "Type-3"
    witnesses: list[str] = []

    for pattern in TYPE0_PATTERNS:
        if pattern.search(source):
            predicted = "Type-0"
            witnesses.append(f"pattern {pattern.pattern!r} in {path.name}")

    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                predicted = _max_class(predicted, "Type-1")
                witnesses.append("async control flow (linear transcript over await steps)")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ("Popen", "run", "system"):
                    predicted = "Type-0"
                    witnesses.append(f"subprocess-style call .{node.func.attr}()")

    memory = {
        "Type-3": "finite explicit modes in solver class",
        "Type-2": "nested call stack via async/task delegation",
        "Type-1": "transcript-linear workspace",
        "Type-0": "container subprocess + filesystem + network envelope",
    }[predicted]

    return ChomskyClassificationV1(
        agent_id=agent_id,
        source_paths=[str(path.resolve())],
        sigma_trace_alphabet_encoding=[],
        predicted_chomsky_class=predicted,
        structural_witnesses=witnesses or ["no Type-0 patterns; finite FSM-style solver assumed"],
        memory_hypothesis=memory,
        vv_obligation_budget=6,
    )
