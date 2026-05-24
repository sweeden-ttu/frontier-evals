#!/usr/bin/env python3
"""Write subdivision_manifest.json for each trace variant from Rogii train data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from paperbench.trace_pipeline.subdivision import (
    build_subdivision_manifest,
    load_rogii_train_frame,
    write_full_subdivision_manifest,
)

VARIANTS = (
    "baseline_column_transformer",
    "typewell_gr_alignment",
    "ps_point_leakage_aware",
    "robust_scale_log1p",
    "parallel_multiwell_loader",
    "formation_plane_spatial",
)

ROGII_DATA = Path("/lustre/work/sweeden/rogii/data")
AGENT_TRACING_EXAMPLES = Path("/lustre/work/sweeden/agent-tracing/examples/rogii/traces/preprocessing")
ROGII_TRACES = Path("/lustre/work/sweeden/rogii/traces/preprocessing")


def variant_out_dirs(variant: str) -> list[Path]:
    return [
        AGENT_TRACING_EXAMPLES / variant,
        ROGII_TRACES / variant,
    ]


def write_for_variant(
    variant: str,
    *,
    data_dir: Path,
    n_splits: int,
    depth_bins: int,
) -> Path:
    train_df = load_rogii_train_frame(data_dir)
    manifest = build_subdivision_manifest(
        variant=variant,
        train_df=train_df,
        n_splits=n_splits,
        depth_bins=depth_bins,
        data_dir=data_dir,
    )
    primary = AGENT_TRACING_EXAMPLES / variant / "subdivision_manifest.json"
    for out_dir in variant_out_dirs(variant):
        out_dir.mkdir(parents=True, exist_ok=True)
        write_full_subdivision_manifest(out_dir / "subdivision_manifest.json", manifest)
    return primary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=VARIANTS, default=None)
    parser.add_argument("--all-variants", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=ROGII_DATA)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--depth-bins", type=int, default=5)
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not args.all_variants and not args.variant:
        parser.error("Specify --variant or --all-variants")

    targets = list(VARIANTS) if args.all_variants else [args.variant]
    for variant in targets:
        out = write_for_variant(
            variant,
            data_dir=args.data_dir,
            n_splits=args.n_splits,
            depth_bins=args.depth_bins,
        )
        if not args.quiet:
            print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
