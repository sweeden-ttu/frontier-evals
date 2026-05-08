"""Optional: HF LogitsProcessor (skipped without ``transformers``)."""

from __future__ import annotations

import pytest

transformers = pytest.importorskip("transformers")
torch = pytest.importorskip("torch")

# pyrefly: ignore [missing-import]
from chomsky_vv.banned import default_policy
# pyrefly: ignore [missing-import]
from chomsky_vv.banned.logits_processor import (
    BannedTokenLogitsProcessor,
    _build_trie,
    _variants,
)


def test_variants_include_leading_space_and_case() -> None:
    out = set(_variants("API_KEY"))
    assert "API_KEY" in out
    assert " API_KEY" in out
    assert "api_key" in out


def test_trie_construction_handles_overlapping_prefixes() -> None:
    trie = _build_trie([(1, 2), (1, 2, 3), (4,)])
    assert 1 in trie
    assert 2 in trie[1]
    assert 3 in trie[1][2]
    assert 4 in trie


def test_logits_processor_pushes_banned_first_token_below_siblings() -> None:
    tokenizer = transformers.AutoTokenizer.from_pretrained("hf-internal-testing/tiny-random-gpt2")
    processor = BannedTokenLogitsProcessor(tokenizer, default_policy(), penalty=-50.0)
    vocab_size = tokenizer.vocab_size
    batch = torch.zeros((1, 1), dtype=torch.long)
    scores = torch.zeros((1, vocab_size), dtype=torch.float)
    out = processor(batch, scores)
    # At least one banned-first token id must have been pushed below 0.
    assert (out < 0).any().item()


def test_logits_processor_hard_mode_sets_neg_inf() -> None:
    tokenizer = transformers.AutoTokenizer.from_pretrained("hf-internal-testing/tiny-random-gpt2")
    processor = BannedTokenLogitsProcessor(tokenizer, default_policy(), hard=True)
    vocab_size = tokenizer.vocab_size
    batch = torch.zeros((1, 1), dtype=torch.long)
    scores = torch.zeros((1, vocab_size), dtype=torch.float)
    out = processor(batch, scores)
    assert torch.isinf(out).any().item()
