"""HF LogitsProcessor that punishes banned token sequences at decode time.

The processor builds a trie from the multi-piece encodings of every
banned token (raw + leading-space + case variants) and, at each decode
step, reduces the next-token logits along every active trie path.

* Soft mode (default): logits along banned paths get an additive
  penalty (configurable via ``policy.logits_soft_penalty``).
* Hard mode: logits are set to ``-inf``. Greedy decoding becomes a
  strict refusal; sampling becomes effectively impossible.

The dependency on :mod:`transformers`/:mod:`torch` is optional. Calling
the constructor without those packages raises ``ImportError`` with an
install hint.
"""

from __future__ import annotations

import math
from typing import Any

from chomsky_vv.banned.policy import BannedTokenPolicy, default_policy

try:  # pragma: no cover - optional import
    from transformers import LogitsProcessor  # type: ignore[import-not-found]

    _HAS_TRANSFORMERS = True
except ImportError:  # pragma: no cover
    _HAS_TRANSFORMERS = False
    LogitsProcessor = object  # type: ignore[assignment, misc]


class BannedTokenLogitsProcessor(LogitsProcessor):  # type: ignore[misc]
    """Apply a banned-sequence trie penalty to next-token logits.

    Args:
        tokenizer: An HF tokenizer (used to encode each banned token
            under multiple variants).
        policy: A :class:`BannedTokenPolicy`. Defaults to the bundled
            default policy.
        penalty: Override the additive logit penalty. Defaults to
            ``policy.logits_soft_penalty`` (typically ``-50``).
        hard: Override the hard-mode flag. ``True`` sets banned logits
            to ``-inf``. Defaults to ``policy.logits_hard_mode``.
    """

    def __init__(
        self,
        tokenizer: Any,
        policy: BannedTokenPolicy | None = None,
        *,
        penalty: float | None = None,
        hard: bool | None = None,
    ) -> None:
        if not _HAS_TRANSFORMERS:
            raise ImportError(
                "BannedTokenLogitsProcessor requires `transformers` and `torch`. "
                "Install via: pip install 'chomsky_vv[training]'"
            )
        self.policy = policy or default_policy()
        if penalty is None:
            penalty = self.policy.logits_soft_penalty
        if hard is None:
            hard = self.policy.logits_hard_mode
        self.hard = bool(hard)
        self.penalty = float("-inf") if self.hard else float(penalty)
        self._tokenizer = tokenizer
        self._sequences: list[tuple[int, ...]] = self._encode_banned(tokenizer)
        self._trie: dict[int, dict] = _build_trie(self._sequences)
        self._max_depth = _max_depth(self._trie)

    # ------------------------------------------------------------------- API
    def __call__(self, input_ids: Any, scores: Any) -> Any:  # pragma: no cover
        """Reduce logits along every active banned-trie path.

        ``input_ids`` has shape ``(batch, seq_len)`` and ``scores`` has
        shape ``(batch, vocab)``. The implementation is deliberately
        small and Python-side; banned tries are tiny so the per-step
        overhead is negligible.
        """
        if not self._trie:
            return scores
        for batch_idx in range(input_ids.shape[0]):
            row = input_ids[batch_idx].tolist()
            self._apply_to_row(row, scores, batch_idx)
        return scores

    # --------------------------------------------------------------- internals
    def _encode_banned(self, tokenizer: Any) -> list[tuple[int, ...]]:
        seqs: list[tuple[int, ...]] = []
        for bt in self.policy.tokens:
            for variant in _variants(bt.token):
                try:
                    ids = tokenizer.encode(variant, add_special_tokens=False)
                except Exception:  # pragma: no cover - tokenizer-dependent
                    continue
                if ids:
                    seqs.append(tuple(int(i) for i in ids))
        seen: set[tuple[int, ...]] = set()
        unique: list[tuple[int, ...]] = []
        for seq in seqs:
            if seq and seq not in seen:
                seen.add(seq)
                unique.append(seq)
        return unique

    def _apply_to_row(self, row: list[int], scores: Any, batch_idx: int) -> None:  # pragma: no cover
        max_depth = self._max_depth or 1
        start = max(0, len(row) - max_depth + 1)
        # Always check the empty-suffix case to penalize banned-first tokens.
        for s in range(start, len(row) + 1):
            node: dict[int, dict] = self._trie
            ok = True
            for tok_id in row[s:]:
                if tok_id in node:
                    node = node[tok_id]  # type: ignore[assignment]
                else:
                    ok = False
                    break
            if not ok:
                continue
            for child_id in node.keys():
                if not isinstance(child_id, int):
                    continue
                if math.isinf(self.penalty):
                    scores[batch_idx, child_id] = float("-inf")
                else:
                    scores[batch_idx, child_id] = (
                        scores[batch_idx, child_id] + self.penalty
                    )


def _variants(token: str) -> list[str]:
    """Generate case + leading-space variants for BPE-style tokenizers."""
    base = {token, token.lower(), token.upper()}
    if token:
        base.add(token[0].upper() + token[1:].lower())
    out: set[str] = set()
    for variant in base:
        out.add(variant)
        out.add(f" {variant}")
    return [v for v in out if v]


def _build_trie(sequences: list[tuple[int, ...]]) -> dict:
    root: dict = {}
    for seq in sequences:
        node = root
        for tok_id in seq:
            node = node.setdefault(tok_id, {})
    return root


def _max_depth(trie: dict) -> int:
    if not trie:
        return 0
    return 1 + max(_max_depth(child) for child in trie.values() if isinstance(child, dict))
