"""P3 — cross-serial dependence detector.

Distinguishes Dyck (CF, Type-2-OK) from cross-serial bracket interleaving
(Type-1+). Requires the alphabet to declare typed pop tokens via
``pairs_with``; otherwise the probe is inconclusive and skipped.
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


class P3CrossSerial(Probe):
    probe_id = "P3"
    targets = frozenset({ChomskyClass.TYPE_2})

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
                notes=f"declared class is {contract.predicted_chomsky_class.value}; P3 targets Type-2",
            )
        pair_map = alphabet.pair_map
        if not pair_map:
            return ProbeResult(
                probe_id=self.probe_id,
                verdict=ProbeVerdict.SKIPPED,
                notes="alphabet declares no typed (paired) pop tokens; P3 inapplicable",
            )
        push = alphabet.push_names
        stack: list[str] = []
        for i, tok in enumerate(trace.tokens):
            if tok.token in push:
                stack.append(tok.token)
                continue
            if tok.token in pair_map:
                expected = pair_map[tok.token]
                actual = stack[-1] if stack else None
                if actual != expected:
                    return ProbeResult(
                        probe_id=self.probe_id,
                        verdict=ProbeVerdict.FAIL,
                        refutes_class=ChomskyClass.TYPE_2,
                        evidence={
                            "index": i,
                            "pop_token": tok.token,
                            "expected_top": expected,
                            "actual_top": actual,
                        },
                        notes="cross-serial bracket interleaving",
                    )
                stack.pop()
        return ProbeResult(
            probe_id=self.probe_id,
            verdict=ProbeVerdict.PASS,
            evidence={"residual_stack_depth": len(stack)},
        )
