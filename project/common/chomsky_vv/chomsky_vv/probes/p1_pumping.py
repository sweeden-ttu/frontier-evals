"""P1 — pumping-lemma refutation for Type-3.

Static realization: any Type-3 (regular) language admits a finite-state
acceptor with bounded pushdown depth (by definition: zero). If the recorded
trace contains push/pop tokens that nest beyond a configurable threshold,
the agent's true language is at least context-free, refuting the Type-3
hypothesis.

This is intentionally a *necessary*-only check. We cannot prove Type-3 from
a single trace; we can only refute it.
"""

from __future__ import annotations

from chomsky_vv.alphabet import Alphabet
from chomsky_vv.probes.base import Probe
from chomsky_vv.schemas import (
    ChomskyClass,
    ChomskyClassification,
    ProbeResult,
    ProbeVerdict,
    TraceRecord,
)


def _max_depth(trace: TraceRecord, alphabet: Alphabet) -> int:
    push = alphabet.push_names
    pop = alphabet.pop_names
    depth = 0
    seen = 0
    for tok in trace.tokens:
        if tok.token in push:
            depth += 1
            seen = max(seen, depth)
        elif tok.token in pop:
            depth -= 1
    return seen


class P1Pumping(Probe):
    probe_id = "P1"
    targets = frozenset({ChomskyClass.TYPE_3})

    def __init__(self, *, depth_threshold: int = 1) -> None:
        if depth_threshold < 0:
            raise ValueError("depth_threshold must be >= 0")
        self.depth_threshold = depth_threshold

    def run(
        self,
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        alphabet: Alphabet,
    ) -> ProbeResult:
        if contract.predicted_chomsky_class != ChomskyClass.TYPE_3:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.SKIPPED,
                notes=f"declared class is {contract.predicted_chomsky_class.value}; P1 targets Type-3",
            )
        if not alphabet.push_names and not alphabet.pop_names:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.INCONCLUSIVE,
                notes="alphabet declares no push/pop tokens; pumping evidence unavailable",
            )
        max_d = _max_depth(trace, alphabet)
        if max_d > self.depth_threshold:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.FAIL,
                refutes_class=ChomskyClass.TYPE_3,
                evidence={"max_depth": max_d, "threshold": self.depth_threshold},
                notes="nested push/pop depth exceeds Type-3 ceiling",
            )
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence={"max_depth": max_d, "threshold": self.depth_threshold},
        )
