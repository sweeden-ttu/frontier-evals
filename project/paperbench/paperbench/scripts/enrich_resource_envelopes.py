#!/usr/bin/env python3
"""Insert resource envelope block and computing-resources evaluation rows into trace CSVs."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from paperbench.chomsky.producer_consumer import CANONICAL_HEADERS
from paperbench.chomsky.resource_envelope import (
    COMPUTING_RESOURCE_EVAL_TOKENS,
    ENVELOPE_ROW_START,
    ENVELOPE_TOKEN,
    EXTENDED_HEADERS,
    envelopes_for_variant,
)
from paperbench.chomsky.trace_csv import insert_type3_consumer_bounds

RESOURCE_COL_START = len(CANONICAL_HEADERS)


def _pad_row(row: list[str], n: int) -> list[str]:
    return (row + [""] * n)[:n]


def _normalize_rows(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return rows
    n = len(rows[0])
    return [_pad_row(row, n) for row in rows]


def _is_envelope_block_present(rows: list[list[str]]) -> bool:
    if len(rows) < 1 + len(CANONICAL_HEADERS):
        return False
    if len(rows[0]) != len(EXTENDED_HEADERS):
        return False
    for i, _agent in enumerate(CANONICAL_HEADERS):
        row = rows[i + 1]
        if len(row) <= i or row[i].strip() != ENVELOPE_TOKEN:
            return False
    return True


def _strip_resource_eval_rows(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return rows
    out = [rows[0]]
    for row in rows[1:]:
        joined = " ".join(row)
        if "evaluate_computing_resources" in joined:
            continue
        out.append(row)
    return out


def _strip_envelope_if_present(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return rows
    header = [h.strip() for h in rows[0]]
    if len(header) == len(EXTENDED_HEADERS) and _is_envelope_block_present(rows):
        body = rows[ENVELOPE_ROW_START + len(CANONICAL_HEADERS) :]
        slim = [row[: len(CANONICAL_HEADERS)] for row in body]
        return [list(CANONICAL_HEADERS)] + _strip_resource_eval_rows([list(CANONICAL_HEADERS)] + slim)[1:]
    if len(header) == len(CANONICAL_HEADERS):
        return _strip_resource_eval_rows(rows)
    return _strip_resource_eval_rows(
        [list(CANONICAL_HEADERS)] + [row[: len(CANONICAL_HEADERS)] for row in rows[1:]]
    )


def _build_envelope_rows(variant: str | None) -> list[list[str]]:
    envs = envelopes_for_variant(variant)
    out: list[list[str]] = []
    for col_idx, agent in enumerate(CANONICAL_HEADERS):
        row = [""] * len(EXTENDED_HEADERS)
        row[col_idx] = ENVELOPE_TOKEN
        suffix = envs[agent].to_row_suffix()
        for j, val in enumerate(suffix):
            row[RESOURCE_COL_START + j] = val
        out.append(row)
    return out


def enrich_trace_csv(path: Path, *, variant: str | None = None) -> list[list[str]]:
    variant = variant or path.parent.name
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    rows = _strip_envelope_if_present(rows)
    body = rows[1:]
    merged = [list(EXTENDED_HEADERS)] + _build_envelope_rows(variant) + body

    record_idx = next(
        (i for i, row in enumerate(merged) if any(c.strip() == "record" for c in row)),
        None,
    )
    if record_idx is not None:
        adr_col = CANONICAL_HEADERS.index("architecture-decision-recorder")
        exp_col = CANONICAL_HEADERS.index("experiment-design-architect")
        eval_rows: list[list[str]] = []
        for tok in COMPUTING_RESOURCE_EVAL_TOKENS:
            row = [""] * len(EXTENDED_HEADERS)
            row[exp_col if "chomsky_rubric" in tok or "bounds" in tok else adr_col] = tok
            eval_rows.append(row)
        cli = [""] * len(EXTENDED_HEADERS)
        cli[adr_col] = (
            "cd /lustre/work/sweeden/rogii && python scripts/evaluate_computing_resources.py "
            f"--trace {path} --variant {variant} -q"
        )
        eval_rows.append(cli)
        merged = merged[:record_idx] + eval_rows + merged[record_idx:]

    merged = insert_type3_consumer_bounds(merged)
    return _normalize_rows(merged)


def write_trace_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--variant", default=None)
    args = parser.parse_args(argv)
    for path in args.paths:
        rows = enrich_trace_csv(path, variant=args.variant)
        write_trace_csv(path, rows)
        print(f"enriched {path} ({len(rows)} rows, {len(rows[0])} cols)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
