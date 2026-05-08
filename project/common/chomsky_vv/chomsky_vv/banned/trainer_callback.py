"""Optional ``transformers`` callback + auxiliary-loss helper.

The :class:`TRLBannedPenaltyCallback` is a thin
:class:`transformers.TrainerCallback` that surfaces the policy size
into the eval metrics; the real work happens in
:func:`compute_banned_logit_penalty`, which is meant to be called from
inside a custom :meth:`Trainer.compute_loss` override::

    class BannedAuxTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False):
            outputs = model(**inputs)
            loss = outputs.loss
            penalty = compute_banned_logit_penalty(
                outputs.logits, self.tokenizer, lambda_=0.1
            )
            return (loss + penalty, outputs) if return_outputs else loss + penalty

The dependency on :mod:`transformers` is optional. Calling either entry
point without that package raises ``ImportError`` with an install hint.
"""

from __future__ import annotations

from typing import Any

from chomsky_vv.banned.matcher import BannedTokenMatcher
from chomsky_vv.banned.policy import BannedTokenPolicy, default_policy

try:  # pragma: no cover - optional import
    from transformers import TrainerCallback  # type: ignore[import-not-found]

    _HAS_TRANSFORMERS = True
except ImportError:  # pragma: no cover
    _HAS_TRANSFORMERS = False
    TrainerCallback = object  # type: ignore[assignment, misc]


class TRLBannedPenaltyCallback(TrainerCallback):  # type: ignore[misc]
    """Surface banned-policy metadata into the trainer's eval metrics.

    The callback is intentionally non-invasive: it does not mutate the
    loss (HF callbacks cannot do that). Pair it with
    :func:`compute_banned_logit_penalty` inside a custom
    ``compute_loss`` to actually penalize banned-first-token mass.
    """

    def __init__(
        self,
        tokenizer: Any,
        policy: BannedTokenPolicy | None = None,
    ) -> None:
        if not _HAS_TRANSFORMERS:
            raise ImportError(
                "TRLBannedPenaltyCallback requires `transformers`. "
                "Install via: pip install 'chomsky_vv[training]'"
            )
        self.tokenizer = tokenizer
        self.policy = policy or default_policy()
        self._matcher = BannedTokenMatcher(self.policy)

    # The signature follows transformers' TrainerCallback API.
    def on_evaluate(  # pragma: no cover - exercised by transformers, not unit tests
        self,
        args: Any,
        state: Any,
        control: Any,
        **kwargs: Any,
    ) -> None:
        metrics = kwargs.get("metrics")
        if isinstance(metrics, dict):
            metrics.setdefault("banned_token/policy_size", len(self.policy.tokens))
            metrics.setdefault("banned_token/lambda", self.policy.rl_lambda)


def compute_banned_logit_penalty(
    logits: Any,
    tokenizer: Any,
    policy: BannedTokenPolicy | None = None,
    *,
    lambda_: float = 1.0,
) -> Any:
    """Return ``lambda * sum(softmax(logits)[banned_first_token_ids])``.

    The result is a torch scalar tensor that can be added directly to
    your training loss. The function never reduces along the batch
    dimension manually — it relies on broadcasting through softmax —
    so the returned value scales naturally with batch size.
    """
    if not _HAS_TRANSFORMERS:
        raise ImportError(
            "compute_banned_logit_penalty requires `transformers` and `torch`."
        )
    import torch  # type: ignore[import-not-found]

    pol = policy or default_policy()
    banned_first_ids: set[int] = set()
    for bt in pol.tokens:
        for variant in (
            bt.token,
            bt.token.lower(),
            bt.token.upper(),
            bt.token.capitalize(),
            f" {bt.token}",
        ):
            try:
                ids = tokenizer.encode(variant, add_special_tokens=False)
            except Exception:  # pragma: no cover
                continue
            if ids:
                banned_first_ids.add(int(ids[0]))
    if not banned_first_ids:
        return torch.tensor(0.0, device=logits.device)
    probs = torch.softmax(logits, dim=-1)
    idx = torch.tensor(
        sorted(banned_first_ids), device=logits.device, dtype=torch.long
    )
    selected = probs.index_select(-1, idx)
    return float(lambda_) * selected.sum()
