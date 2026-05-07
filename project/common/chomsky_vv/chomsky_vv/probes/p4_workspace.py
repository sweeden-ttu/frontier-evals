"""P4 — workspace linearity for Type-1.

Type-1 (linear-bounded) requires transcript size to grow at most linearly
with input size. We fit a log-log slope across multiple traces of varying
input length; a slope above tolerance refutes Type-1 in favor of Type-0.

This is the only probe that needs more than one trace; the harness threads
``length_traces`` and ``length_inputs`` through.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from chomsky_vv.schemas import (
    ChomskyClass,
    ChomskyClassification,
    ProbeResult,
    ProbeVerdict,
    TraceRecord,
)


def _least_squares_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


class P4WorkspaceLinearity:
    probe_id = "P4"
    targets = frozenset({ChomskyClass.TYPE_1})

    def __init__(self, *, slope_tolerance: float = 1.5, min_traces: int = 3) -> None:
        if slope_tolerance <= 1.0:
            raise ValueError("slope_tolerance must be > 1.0; linear growth has slope 1.0")
        if min_traces < 2:
            raise ValueError("min_traces must be >= 2 for any fit")
        self.slope_tolerance = slope_tolerance
        self.min_traces = min_traces

    def run(
        self,
        *,
        contract: ChomskyClassification,
        traces: Sequence[TraceRecord],
        input_lengths: Sequence[int],
    ) -> ProbeResult:
        if contract.predicted_chomsky_class != ChomskyClass.TYPE_1:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.SKIPPED,
                notes=f"declared class is {contract.predicted_chomsky_class.value}; P4 targets Type-1",
            )
        if len(traces) < self.min_traces or len(input_lengths) != len(traces):
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.INCONCLUSIVE,
                notes=(
                    f"need >= {self.min_traces} traces with matching input_lengths; "
                    f"got traces={len(traces)} lengths={len(input_lengths)}"
                ),
            )
        sizes = [len(t.tokens) for t in traces]
        xs = [math.log(max(L, 1)) for L in input_lengths]
        ys = [math.log(max(s, 1)) for s in sizes]
        slope = _least_squares_slope(xs, ys)
        evidence = {
            "loglog_slope": slope,
            "tolerance": self.slope_tolerance,
            "input_lengths": list(input_lengths),
            "transcript_sizes": sizes,
        }
        if slope > self.slope_tolerance:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.FAIL,
                refutes_class=ChomskyClass.TYPE_1,
                evidence=evidence,
                notes="transcript size grows super-linearly with input length",
            )
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence=evidence,
        )
