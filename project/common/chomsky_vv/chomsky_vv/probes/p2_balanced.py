"""P2 — Dyck balance + bounded pushdown depth for Type-2.

Refutes Type-2 if the trace is unbalanced (pop without matching push, or
non-empty residual stack), or if the observed depth exceeds the contract's
declared bound when one is supplied.
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


class P2BalancedDepth(Probe):
    probe_id = "P2"
    targets = frozenset({ChomskyClass.TYPE_2})

    def __init__(self, *, declared_max_depth: int | None = None) -> None:
        if declared_max_depth is not None and declared_max_depth < 0:
            raise ValueError("declared_max_depth must be >= 0")
        self.declared_max_depth = declared_max_depth

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
                notes=f"declared class is {contract.predicted_chomsky_class.value}; P2 targets Type-2",
            )
        push = alphabet.push_names
        pop = alphabet.pop_names
        if not push or not pop:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.INCONCLUSIVE,
                notes="alphabet declares no push/pop tokens; cannot verify Dyck balance",
            )
        depth = 0
        max_d = 0
        for i, tok in enumerate(trace.tokens):
            if tok.token in push:
                depth += 1
            elif tok.token in pop:
                depth -= 1
            if depth < 0:
                return ProbeResult(
                    probe_id=self.probe_id,
                    verdict=ProbeVerdict.FAIL,
                    refutes_class=ChomskyClass.TYPE_2,
                    evidence={"unbalanced_at": i, "token": tok.token},
                    notes="pop without matching push (Dyck imbalance)",
                )
            max_d = max(max_d, depth)
        if depth != 0:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.FAIL,
                refutes_class=ChomskyClass.TYPE_2,
                evidence={"final_depth": depth, "max_depth": max_d},
                notes="trace ended with non-empty stack",
            )
        if self.declared_max_depth is not None and max_d > self.declared_max_depth:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.FAIL,
                refutes_class=ChomskyClass.TYPE_2,
                evidence={"max_depth": max_d, "declared_max_depth": self.declared_max_depth},
                notes="observed pushdown depth exceeds declared bound",
            )
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence={"max_depth": max_d, "balanced": True},
        )
