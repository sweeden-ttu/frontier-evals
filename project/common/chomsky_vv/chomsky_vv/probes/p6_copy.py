"""P6 — copy-language boundary.

The copy language ``{ww | w ∈ Σ*}`` is not context-free. If a trace
contains a contiguous repetition of a non-trivial fragment, the underlying
language is at least Type-1, refuting Type-2.

Search is bounded to ``min_copy_length <= L <= max_copy_length`` and
``O(n^2)`` worst-case, which is acceptable for trace sizes encountered in
practice (paperbench/swelancer/evmbench traces are O(10^3) tokens).
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


class P6CopyLanguage(Probe):
    probe_id = "P6"
    targets = frozenset({ChomskyClass.TYPE_2})

    def __init__(self, *, min_copy_length: int = 4, max_copy_length: int | None = None) -> None:
        if min_copy_length < 2:
            raise ValueError("min_copy_length must be >= 2 (single-token repeats are not informative)")
        if max_copy_length is not None and max_copy_length < min_copy_length:
            raise ValueError("max_copy_length must be >= min_copy_length")
        self.min_copy_length = min_copy_length
        self.max_copy_length = max_copy_length

    def run(
        self,
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        alphabet: Alphabet,
    ) -> ProbeResult:
        if contract.predicted_chomsky_class != ChomskyClass.TYPE_2:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.SKIPPED,
                notes=f"declared class is {contract.predicted_chomsky_class.value}; P6 targets Type-2",
            )
        s = [t.token for t in trace.tokens]
        n = len(s)
        upper = self.max_copy_length if self.max_copy_length is not None else n // 2
        for L in range(self.min_copy_length, min(upper, n // 2) + 1):
            for start in range(0, n - 2 * L + 1):
                if s[start : start + L] == s[start + L : start + 2 * L]:
                    return ProbeResult(
                        probe_id=self.probe_id,
                        verdict=ProbeVerdict.FAIL,
                        refutes_class=ChomskyClass.TYPE_2,
                        evidence={
                            "copy_start": start,
                            "copy_length": L,
                            "fragment": s[start : start + L],
                        },
                        notes="exact ww copy detected; refutes context-free",
                    )
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence={"trace_length": n, "min_copy_length": self.min_copy_length},
        )
