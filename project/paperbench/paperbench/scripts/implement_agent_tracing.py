#!/usr/bin/env python3
"""Implement and validate agent-tracing paper artifacts (local, no Docker)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from paperbench.chomsky.hooks import analyze_trace_and_verify, run_field_analysis_on_solver
from paperbench.chomsky.schema import contracts_dir
from paperbench.trace_pipeline.paths import discover_variants, resolve_trace_path


def validate_all_traces(*, variants: tuple[str, ...] | None = None) -> int:
    if variants is None:
        variants = discover_variants()
    results = []
    failures = 0
    for variant in variants:
        trace_path = resolve_trace_path(variant)
        if not trace_path.exists():
            print(f"MISSING {trace_path}")
            failures += 1
            continue
        summary = analyze_trace_and_verify(trace_path)
        valid = summary["validation"]["valid"]
        cls = summary["classification"]["predicted_chomsky_class"]
        passed = summary["verification"]["checks"]
        ok = valid and all(c["status"] == "PASS" for c in passed)
        status = "OK" if ok else "FAIL"
        print(f"{status} {variant}: class={cls} valid={valid}")
        if not ok:
            failures += 1
        results.append(summary)

    out = contracts_dir() / "rogii_validation_summary.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return failures


def analyze_dummy_solver() -> None:
    run_field_analysis_on_solver("paperbench.solvers.dummy.solver:PaperBenchDummySolver")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant",
        action="append",
        dest="variants",
        help="Validate one variant (repeatable). Default: all discovered variants.",
    )
    parser.add_argument(
        "--validate-traces",
        action="store_true",
        help="Validate and classify all six Rogii preprocessing trace variants.",
    )
    parser.add_argument(
        "--analyze-dummy-solver",
        action="store_true",
        help="Run Chomsky field analysis on PaperBenchDummySolver.",
    )
    args = parser.parse_args()

    if not args.validate_traces and not args.analyze_dummy_solver:
        parser.print_help()
        return 0

    rc = 0
    if args.validate_traces:
        selected = tuple(args.variants) if args.variants else None
        rc = validate_all_traces(variants=selected)
    if args.analyze_dummy_solver:
        analyze_dummy_solver()
    return rc


if __name__ == "__main__":
    sys.exit(main())
