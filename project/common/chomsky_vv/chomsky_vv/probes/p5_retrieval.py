"""P5 — retrieval-swap ablation.

A purely-retrieval-grounded agent should produce identical token sequences
when its underlying corpus is replaced by an adversarial-but-shape-equivalent
corpus. Comparing two traces in this probe yields a coarse Hamming-style
delta over the token stream; deviation above tolerance signals that the
agent is doing more than retrieval (reasoning, memorization, etc.) and the
Type-0 contract's "retrieval purity" claim is refuted.

True retrieval-swap requires re-running the agent — out of scope for the
static harness. This probe is INCONCLUSIVE without a paired baseline trace.
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


class P5RetrievalSwap(Probe):
    probe_id = "P5"
    targets = frozenset({ChomskyClass.TYPE_0})

    def __init__(self, *, divergence_tolerance: float = 0.10) -> None:
        if not 0.0 <= divergence_tolerance <= 1.0:
            raise ValueError("divergence_tolerance must be in [0, 1]")
        self.divergence_tolerance = divergence_tolerance

    def run(
        self,
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        alphabet: Alphabet,
        baseline_trace: TraceRecord | None = None,
    ) -> ProbeResult:
        if baseline_trace is None:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.SKIPPED,
                notes="P5 requires a paired baseline trace",
            )
        a = [t.token for t in baseline_trace.tokens]
        b = [t.token for t in trace.tokens]
        n = max(len(a), len(b))
        if n == 0:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.INCONCLUSIVE,
                notes="both traces empty",
            )
        a += [""] * (n - len(a))
        b += [""] * (n - len(b))
        diffs = sum(1 for x, y in zip(a, b) if x != y)
        divergence = diffs / n
        evidence = {"divergence": divergence, "tolerance": self.divergence_tolerance, "length": n}
        if divergence > self.divergence_tolerance:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.FAIL,
                refutes_class=ChomskyClass.TYPE_0,
                evidence=evidence,
                notes="behavior diverges under retrieval swap; non-retrieval reasoning present",
            )
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence=evidence,
        )
