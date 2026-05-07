"""Probe interface.

Each probe consumes a Chomsky classification contract plus auxiliary inputs
and emits a ``ProbeResult``. Probes never raise on declared-class mismatch:
they return a SKIPPED verdict so the harness can record the full obligation
matrix even when an obligation is inapplicable to a given agent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from chomsky_vv.alphabet import Alphabet
from chomsky_vv.schemas import (
    ChomskyClass,
    ChomskyClassification,
    ProbeResult,
    TraceRecord,
)


class Probe(ABC):
    probe_id: str = ""
    targets: frozenset[ChomskyClass] = frozenset()

    @abstractmethod
    def run(
        self,
        *,
        contract: ChomskyClassification,
        trace: TraceRecord,
        alphabet: Alphabet,
    ) -> ProbeResult: ...
