from __future__ import annotations

import pytest

from chomsky_vv import Alphabet, TokenSpec, TraceRecorder


def _abc_alphabet() -> Alphabet:
    return Alphabet(
        tokens=[
            TokenSpec(name="open", pattern=r"\(", push=True),
            TokenSpec(name="close", pattern=r"\)", pop=True, pairs_with="open"),
            TokenSpec(name="bash", pattern=r"BASH"),
        ]
    )


def test_alphabet_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        Alphabet(tokens=[TokenSpec(name="x", pattern="a"), TokenSpec(name="x", pattern="b")])


def test_alphabet_rejects_bad_pairs_with() -> None:
    with pytest.raises(ValueError, match="not in alphabet"):
        Alphabet(
            tokens=[
                TokenSpec(name="close", pattern=r"\)", pop=True, pairs_with="missing"),
            ]
        )


def test_token_spec_validates_name_identifier() -> None:
    with pytest.raises(ValueError, match="identifier"):
        TokenSpec(name="bad name", pattern="x")


def test_token_spec_pop_only_pairs() -> None:
    with pytest.raises(ValueError, match="pairs_with"):
        TokenSpec(name="t", pattern="a", pairs_with="other")


def test_alphabet_scan_in_order() -> None:
    a = _abc_alphabet()
    hits = a.scan("(BASH(BASH))")
    names = [h[0].name for h in hits]
    assert names == ["open", "bash", "open", "bash", "close", "close"]


def test_recorder_records_and_round_trips_jsonl(tmp_path) -> None:
    a = _abc_alphabet()
    rec = TraceRecorder(agent_id="harness.py", run_id="r1", alphabet=a)
    rec.record("open", payload="(")
    rec.record("bash", payload="BASH")
    rec.record("close", payload=")")
    out = rec.to_jsonl(tmp_path / "trace.jsonl")
    rec2 = TraceRecorder.from_jsonl(out, agent_id="pb.test", run_id="r1", alphabet=a)
    t1 = rec.trace()
    t2 = rec2.trace()
    assert [tk.token for tk in t1.tokens] == [tk.token for tk in t2.tokens]
    assert t1.tokens[0].payload_hash is not None


def test_recorder_record_text_uses_alphabet() -> None:
    a = _abc_alphabet()
    rec = TraceRecorder(agent_id="alphabet.py", run_id="r2", alphabet=a)
    rec.record_text("ignored (BASH) ignored (BASH)")
    tokens = [t.token for t in rec.trace().tokens]
    assert tokens == ["open", "bash", "close", "open", "bash", "close"]


def test_recorder_rejects_unknown_token() -> None:
    a = _abc_alphabet()
    rec = TraceRecorder(agent_id="harness.py", run_id="r3", alphabet=a)
    with pytest.raises(ValueError, match="not in alphabet"):
        rec.record("unknown")
