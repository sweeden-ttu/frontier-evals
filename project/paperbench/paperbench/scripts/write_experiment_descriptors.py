#!/usr/bin/env python3
"""Write experiment_descriptor.json + paper_refs.md for Rogii trace variants."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from paperbench.trace_pipeline.experiment_descriptor import (
    VARIANT_BASE_PAPERS,
    build_experiment_descriptor,
    render_paper_refs_md,
    variant_dir,
    write_experiment_descriptor,
    write_paper_refs_md,
)
from paperbench.trace_pipeline.paths import discover_variants, resolve_rogii_root

AGENT_TRACING_TRACE_BASELINE = Path("/lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii/traces/preprocessing")
AGENT_TRACING_VARIANTS = Path("/lustre/work/sweeden/agent-tracing/examples/rogii/traces/preprocessing")
ROGII_VARIANTS = Path("/lustre/work/sweeden/rogii/traces/preprocessing")


def _primary_rogii_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    for candidate in (AGENT_TRACING_TRACE_BASELINE, AGENT_TRACING_VARIANTS, ROGII_VARIANTS):
        if candidate.is_dir():
            return candidate.parent.parent
    return resolve_rogii_root()


def _ablation_factors(variant: str, vdir: Path) -> list[dict] | None:
    plan_path = vdir / "ablation_plan.json"
    if not plan_path.is_file():
        return None
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    return plan.get("ablation_factors")


def write_variant(variant: str, *, rogii_root: Path, mirror_roots: list[Path]) -> list[Path]:
    vdir = variant_dir(variant, rogii_root=rogii_root)
    factors = _ablation_factors(variant, vdir)
    desc_path = write_experiment_descriptor(
        variant, out_dir=vdir, rogii_root=rogii_root, ablation_factors=factors
    )
    descriptor = build_experiment_descriptor(
        variant, rogii_root=rogii_root, ablation_factors=factors
    )
    refs_path = write_paper_refs_md(descriptor, out_dir=vdir)
    written = [desc_path, refs_path]

    for mirror in mirror_roots:
        dest = mirror / variant
        if dest.resolve() == vdir.resolve():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        for src in (desc_path, refs_path):
            tgt = dest / src.name
            if tgt.resolve() == src.resolve():
                continue
            shutil.copy2(src, tgt)
            written.append(tgt)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(VARIANT_BASE_PAPERS))
    parser.add_argument("--all-variants", action="store_true")
    parser.add_argument("--rogii-root", type=Path, default=None)
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not args.all_variants and not args.variant:
        parser.error("specify --variant or --all-variants")

    rogii_root = _primary_rogii_root(args.rogii_root)
    variants = discover_variants() if args.all_variants else (args.variant,)
    preprocess_root = (rogii_root / "traces" / "preprocessing").resolve()
    mirrors = [
        p
        for p in (AGENT_TRACING_VARIANTS, ROGII_VARIANTS, Path(resolve_rogii_root()) / "traces" / "preprocessing")
        if p.is_dir() and p.resolve() != preprocess_root
    ]
    # Deduplicate mirror paths
    seen: set[Path] = set()
    unique_mirrors: list[Path] = []
    for p in mirrors:
        r = p.resolve()
        if r not in seen:
            seen.add(r)
            unique_mirrors.append(p)
    mirrors = unique_mirrors

    for variant in variants:
        if variant not in VARIANT_BASE_PAPERS:
            print(f"skip unknown variant {variant}", file=sys.stderr)
            continue
        paths = write_variant(variant, rogii_root=rogii_root, mirror_roots=mirrors)
        if not args.quiet:
            for p in paths[:2]:
                print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
