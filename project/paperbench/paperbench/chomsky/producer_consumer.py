"""Producer swim lanes must be bounded by Type-3 consumer gates."""

from __future__ import annotations

from dataclasses import dataclass

# Canonical Rogii swim-lane headers (20 columns).
CANONICAL_HEADERS: tuple[str, ...] = (
    "data_downloader",
    "schema-sentinel",
    "eda_profiler",
    "well_group_detector",
    "target_diagnostician",
    "feature_engineer",
    "preprocessor",
    "cv_orchestrator",
    "model_trainer",
    "model_ensembler",
    "predictor",
    "oof_evaluator",
    "error_analyzer",
    "submission_formatter",
    "submission_validator",
    "kaggle_submitter",
    "seed-control-officer",
    "experiment-design-architect",
    "architecture-decision-recorder",
    "dependency-graph-orchestrator",
)

# Type-3 consumer columns (finite-state schema validators).
TYPE3_CONSUMER_COLUMNS: frozenset[int] = frozenset({1, 14})  # schema-sentinel, submission_validator

# All other swim lanes are treated as producer-capable (Type-0 envelope when CLI present).
PRODUCER_COLUMNS: frozenset[int] = frozenset(range(20)) - TYPE3_CONSUMER_COLUMNS - {19}

# Producer column index -> Type-3 consumer column index.
CONSUMER_FOR_PRODUCER: dict[int, int] = {}
for _col in PRODUCER_COLUMNS:
    if _col in {10, 13, 15}:  # predictor, submission_formatter, kaggle_submitter
        CONSUMER_FOR_PRODUCER[_col] = 14
    else:
        CONSUMER_FOR_PRODUCER[_col] = 1

TYPE3_CONSUMER_PREFIX = "type3_consumer_bound_"


@dataclass(frozen=True)
class ProducerConsumerPair:
    producer_col: int
    producer_name: str
    consumer_col: int
    consumer_name: str
    bound_token: str


def bound_token_for_producer(producer_col: int) -> str:
    name = CANONICAL_HEADERS[producer_col]
    slug = name.replace("-", "_")
    return f"{TYPE3_CONSUMER_PREFIX}{slug}"


def all_producer_consumer_pairs() -> list[ProducerConsumerPair]:
    pairs: list[ProducerConsumerPair] = []
    for prod in sorted(PRODUCER_COLUMNS):
        cons = CONSUMER_FOR_PRODUCER[prod]
        pairs.append(
            ProducerConsumerPair(
                producer_col=prod,
                producer_name=CANONICAL_HEADERS[prod],
                consumer_col=cons,
                consumer_name=CANONICAL_HEADERS[cons],
                bound_token=bound_token_for_producer(prod),
            )
        )
    return pairs


def is_type3_consumer_token(value: str) -> bool:
    return value.startswith(TYPE3_CONSUMER_PREFIX) or value.startswith("type3_consumer_validate")


def consumer_token_for_row(producer_col: int, *, cli: bool = False) -> str:
    base = bound_token_for_producer(producer_col)
    if cli:
        return f"{base}_after_cli"
    return base
