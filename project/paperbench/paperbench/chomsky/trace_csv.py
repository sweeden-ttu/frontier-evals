from __future__ import annotations

import csv
import re
from pathlib import Path

from paperbench.chomsky.producer_consumer import (
    CANONICAL_HEADERS,
    CONSUMER_FOR_PRODUCER,
    PRODUCER_COLUMNS,
    bound_token_for_producer,
    is_type3_consumer_token,
)
from paperbench.chomsky.resource_envelope import (
    ENVELOPE_ROW_COUNT,
    ENVELOPE_ROW_START,
    ENVELOPE_TOKEN,
    EXTENDED_HEADERS,
    RESOURCE_ENVELOPE_COLUMNS,
    VALID_CHOMSKY_TYPES,
    VALID_CONTEXT_POLICIES,
    VALID_LTM,
    VALID_LTM_BOUNDS,
    COMPUTING_RESOURCE_EVAL_TOKENS,
    validate_resource_envelope_rows,
)
from paperbench.chomsky.schema import ValidationReport

# Legacy 20-column traces: governance rows 2-4 (0-based indices 1-3).
LEGACY_GOVERNANCE_ROW_INDICES = {1, 2, 3}
EXTENDED_GOVERNANCE_ROW_INDICES = {
    ENVELOPE_ROW_START + ENVELOPE_ROW_COUNT,
    ENVELOPE_ROW_START + ENVELOPE_ROW_COUNT + 1,
    ENVELOPE_ROW_START + ENVELOPE_ROW_COUNT + 2,
}

CLOSURE_TOKENS = frozenset(
    {
        "serialize_markdown",
        "topological_order",
        "record",
        "record_initial_adr",
        "dispatch",
    }
)
CLI_PATTERN = re.compile(
    r"\b(kaggle|sbatch|uv\s+pip|curl|wget|python\s+|conda\s+|docker\s+|git\s+)",
    re.IGNORECASE,
)
RESOURCE_EVAL_TOKEN_PREFIX = "evaluate_computing_resources"


def _non_empty_cells(row: list[str], *, max_col: int | None = None) -> list[tuple[int, str]]:
    limit = len(row) if max_col is None else min(max_col, len(row))
    return [(i, cell.strip()) for i, cell in enumerate(row[:limit]) if cell.strip()]


def _is_extended_format(header: list[str]) -> bool:
    return len(header) == len(EXTENDED_HEADERS)


def _governance_indices(rows: list[list[str]]) -> set[int]:
    if rows and _is_extended_format([h.strip() for h in rows[0]]):
        return set(EXTENDED_GOVERNANCE_ROW_INDICES)
    return set(LEGACY_GOVERNANCE_ROW_INDICES)


def _envelope_indices(rows: list[list[str]]) -> set[int]:
    if not rows or not _is_extended_format([h.strip() for h in rows[0]]):
        return set()
    return set(range(ENVELOPE_ROW_START, ENVELOPE_ROW_START + ENVELOPE_ROW_COUNT))


def _skip_pipeline_rules(row_idx: int, rows: list[list[str]]) -> bool:
    """Rows exempt from single-action pipeline rules."""
    if row_idx in _envelope_indices(rows):
        return True
    if row_idx in _governance_indices(rows):
        return True
    if row_idx < len(rows):
        row = rows[row_idx]
        if any(c.strip() == ENVELOPE_TOKEN for c in row[: len(CANONICAL_HEADERS)]):
            return True
        if any(c.strip().startswith(RESOURCE_EVAL_TOKEN_PREFIX) for c in row):
            return True
        if any(c.strip() in COMPUTING_RESOURCE_EVAL_TOKENS for c in row):
            return True
        if any(c.strip().startswith("validate_resource_bounds") for c in row):
            return True
        if any(c.strip().startswith("validate_slurm_envelope") for c in row):
            return True
        if any("evaluate_computing_resources.py" in c for c in row):
            return True
    return False


def validate_trace_language_csv(
    path: Path | str,
    *,
    require_canonical_header: bool = True,
) -> ValidationReport:
    path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return ValidationReport(path=str(path), valid=False, errors=["file not found"])

    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if not rows:
        return ValidationReport(path=str(path), valid=False, errors=["empty CSV"])

    header = [h.strip() for h in rows[0]]
    column_count = len(header)
    extended = _is_extended_format(header)
    swim_cols = len(CANONICAL_HEADERS)

    if column_count not in (swim_cols, len(EXTENDED_HEADERS)):
        errors.append(f"expected {swim_cols} or {len(EXTENDED_HEADERS)} columns, got {column_count}")

    if require_canonical_header:
        expected = EXTENDED_HEADERS if extended else CANONICAL_HEADERS
        if tuple(header) != expected:
            errors.append("header does not match canonical Rogii swim-lane names (+ resource envelope columns)")

    if extended:
        errors.extend(validate_resource_envelope_rows(rows))

    found_closure = False
    has_cli = False
    found_resource_eval = False

    for row_idx, row in enumerate(rows[1:], start=2):
        zero_idx = row_idx - 1
        if len(row) != column_count:
            row = (row + [""] * column_count)[:column_count]

        cells = _non_empty_cells(row)
        swim_cells = _non_empty_cells(row, max_col=swim_cols)

        for _, value in cells:
            if value in CLOSURE_TOKENS:
                found_closure = True
            if CLI_PATTERN.search(value):
                has_cli = True
            if value.startswith(RESOURCE_EVAL_TOKEN_PREFIX) or value in COMPUTING_RESOURCE_EVAL_TOKENS:
                found_resource_eval = True

        if _skip_pipeline_rules(zero_idx, rows):
            continue

        if extended:
            resource_tail = row[swim_cols:]
            if any(c.strip() for c in resource_tail):
                errors.append(f"row {row_idx}: pipeline row must leave resource envelope columns empty")

        if len(swim_cells) > 1:
            errors.append(
                f"row {row_idx}: expected single-action row, found {len(swim_cells)} cells: "
                f"{[v for _, v in swim_cells]}"
            )

    if not found_closure:
        errors.append("pipeline closure tokens not found in dependency-graph-orchestrator column")

    if extended and not found_resource_eval:
        errors.append("computing resources evaluation block missing (Chomsky formal agent rubric)")

    if has_cli:
        warnings.append("CLI/subprocess patterns detected (Type-0 envelope evidence)")

    pc_errors = validate_producer_type3_consumer_bounds(rows)
    errors.extend(pc_errors)

    return ValidationReport(
        path=str(path),
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        column_count=column_count,
        row_count=len(rows),
        agent_columns=header[:swim_cols],
    )


def collect_alphabet(path: Path | str) -> list[str]:
    """Finite discretization Sigma: unique non-empty cell tokens."""
    path = Path(path)
    tokens: set[str] = set()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            for cell in row[: len(CANONICAL_HEADERS)]:
                cell = cell.strip()
                if cell and cell != ENVELOPE_TOKEN:
                    tokens.add(cell)
    return sorted(tokens)


def validate_producer_type3_consumer_bounds(rows: list[list[str]]) -> list[str]:
    """Every producer swim lane must have Type-3 consumer bounds; CLI rows need immediate consumer."""
    errors: list[str] = []
    if len(rows) < 2:
        return errors

    record_idx = None
    for i, row in enumerate(rows):
        if any(c.strip() == "record" for c in row):
            record_idx = i
            break
    if record_idx is None:
        return errors

    gov = _governance_indices(rows)
    env = _envelope_indices(rows)

    for prod_col in sorted(PRODUCER_COLUMNS):
        consumer_col = CONSUMER_FOR_PRODUCER[prod_col]
        prod_name = CANONICAL_HEADERS[prod_col]
        bound = bound_token_for_producer(prod_col)
        prod_rows = [
            i
            for i in range(1, record_idx)
            if i not in gov
            and i not in env
            and not _skip_pipeline_rules(i, rows)
            and len(rows[i]) > prod_col
            and rows[i][prod_col].strip()
            and not is_type3_consumer_token(rows[i][prod_col].strip())
            and rows[i][prod_col].strip() != ENVELOPE_TOKEN
        ]
        if not prod_rows:
            continue
        consumer_hits = [
            rows[i][consumer_col].strip()
            for i in range(1, record_idx)
            if len(rows[i]) > consumer_col and is_type3_consumer_token(rows[i][consumer_col].strip())
        ]
        if not any(bound in t or prod_name.replace("-", "_") in t for t in consumer_hits):
            errors.append(
                f"producer '{prod_name}' missing Type-3 consumer bound (expected {bound!r} in "
                f"'{CANONICAL_HEADERS[consumer_col]}')"
            )

    for i in range(1, record_idx):
        if i in gov or i in env or _skip_pipeline_rules(i, rows):
            continue
        row = rows[i]
        for prod_col, val in _non_empty_cells(row, max_col=len(CANONICAL_HEADERS)):
            if prod_col not in PRODUCER_COLUMNS:
                continue
            if not CLI_PATTERN.search(val):
                continue
            consumer_col = CONSUMER_FOR_PRODUCER[prod_col]
            if i + 1 >= len(rows):
                errors.append(
                    f"row {i + 1}: CLI producer in '{CANONICAL_HEADERS[prod_col]}' has no following consumer"
                )
                continue
            nxt = rows[i + 1]
            if len(nxt) <= consumer_col or not is_type3_consumer_token(nxt[consumer_col].strip()):
                errors.append(
                    f"row {i + 1}: CLI in '{CANONICAL_HEADERS[prod_col]}' must be immediately "
                    f"bounded by Type-3 consumer in '{CANONICAL_HEADERS[consumer_col]}'"
                )
    return errors


def insert_type3_consumer_bounds(rows: list[list[str]]) -> list[list[str]]:
    """Insert Type-3 consumer rows bounding producer swim lanes and CLI steps."""
    if not rows:
        return rows

    cleaned: list[list[str]] = [rows[0]]
    for row in rows[1:]:
        cells = _non_empty_cells(row)
        if len(cells) == 1 and is_type3_consumer_token(cells[0][1]):
            continue
        cleaned.append(row)
    rows = cleaned

    ncol = len(rows[0])
    record_idx = len(rows)
    for i, row in enumerate(rows):
        if any(c.strip() == "record" for c in row):
            record_idx = i
            break

    gov = _governance_indices(rows)
    out: list[list[str]] = [rows[0]]
    seen_lane_bound: set[int] = set()

    for i in range(1, record_idx):
        row = (rows[i] + [""] * ncol)[:ncol]
        out.append(row)
        if i in gov or i in _envelope_indices(rows) or _skip_pipeline_rules(i, rows):
            continue
        cells = _non_empty_cells(row, max_col=len(CANONICAL_HEADERS))
        if len(cells) != 1:
            continue
        prod_col, val = cells[0]
        if prod_col not in PRODUCER_COLUMNS or is_type3_consumer_token(val):
            continue
        consumer_col = CONSUMER_FOR_PRODUCER[prod_col]
        if CLI_PATTERN.search(val):
            token = f"{bound_token_for_producer(prod_col)}_after_cli"
            cons_row = [""] * ncol
            cons_row[consumer_col] = token
            out.append(cons_row)
        elif prod_col not in seen_lane_bound:
            token = bound_token_for_producer(prod_col)
            cons_row = [""] * ncol
            cons_row[consumer_col] = token
            out.append(cons_row)
            seen_lane_bound.add(prod_col)

    active: set[int] = set()
    bounds_present: set[str] = set()
    for row in out:
        for j, c in enumerate(row[: len(CANONICAL_HEADERS)]):
            cs = c.strip()
            if is_type3_consumer_token(cs):
                bounds_present.add(cs)
            if j in PRODUCER_COLUMNS and cs and not is_type3_consumer_token(cs):
                active.add(j)

    for prod_col in sorted(active):
        token = bound_token_for_producer(prod_col)
        if token not in bounds_present and f"{token}_after_cli" not in bounds_present:
            consumer_col = CONSUMER_FOR_PRODUCER[prod_col]
            cons_row = [""] * ncol
            cons_row[consumer_col] = token
            out.append(cons_row)

    out.extend(rows[record_idx:])
    return out
