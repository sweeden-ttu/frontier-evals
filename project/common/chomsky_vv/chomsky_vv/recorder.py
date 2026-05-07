"""Σ-trace recorder.

Producer side of the Chomsky V&V contract bus: emits ``sigma_trace_v1``
records that downstream consumers (probe harness, monitor adapters,
embedding learning loop) read against a pinned alphabet.

Two recording modes are supported:

  * **Direct** — instrumentation points in agent code call ``record(name, …)``
    at a tool-call boundary. Best for live agents that we control.
  * **Post-hoc** — ``record_text(blob)`` discretizes a free-text log via the
    alphabet's pattern matcher. Best for replaying existing logs (e.g.
    ``runs_dir/<group>/<run>/agent.log`` from PaperBench).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chomsky_vv.alphabet import Alphabet
from chomsky_vv.schemas import TraceRecord, TraceToken


def _hash(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class TraceRecorder:
    agent_id: str
    run_id: str
    alphabet: Alphabet
    _seq: int = field(default=0, init=False)
    _tokens: list[TraceToken] = field(default_factory=list, init=False)

    def record(
        self,
        token: str,
        *,
        payload: str | bytes | None = None,
        source_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceToken:
        if token not in self.alphabet.names:
            raise ValueError(f"token {token!r} not in alphabet {self.alphabet.names}")
        tok = TraceToken(
            token=token,
            ts_seq=self._seq,
            payload_hash=_hash(payload) if payload is not None else None,
            source_ref=source_ref,
            metadata=metadata or {},
        )
        self._seq += 1
        self._tokens.append(tok)
        return tok

    def record_text(self, text: str, *, source_ref: str | None = None) -> list[TraceToken]:
        out: list[TraceToken] = []
        for spec, start, end in self.alphabet.scan(text):
            out.append(
                self.record(
                    spec.name,
                    payload=text[start:end],
                    source_ref=source_ref,
                    metadata={"start": start, "end": end},
                )
            )
        return out

    def trace(self) -> TraceRecord:
        return TraceRecord(
            agent_id=self.agent_id,
            run_id=self.run_id,
            alphabet_names=self.alphabet.names,
            tokens=list(self._tokens),
        )

    def to_jsonl(self, path: Path | str) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for t in self._tokens:
                fh.write(json.dumps(t.model_dump(), sort_keys=True))
                fh.write("\n")
        return p

    @classmethod
    def from_jsonl(
        cls,
        path: Path | str,
        *,
        agent_id: str,
        run_id: str,
        alphabet: Alphabet,
    ) -> TraceRecorder:
        rec = cls(agent_id=agent_id, run_id=run_id, alphabet=alphabet)
        with Path(path).open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                tok = TraceToken.model_validate_json(line)
                rec._tokens.append(tok)
                rec._seq = max(rec._seq, tok.ts_seq + 1)
        return rec
