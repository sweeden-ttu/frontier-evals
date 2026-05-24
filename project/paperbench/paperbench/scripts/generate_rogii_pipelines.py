#!/usr/bin/env python3
"""Generate Rogii ML pipelines and Slurm submit wrappers from frontier.yaml.

Reads ``/lustre/work/sweeden/frontier-evals/frontier.yaml`` (``rogii_pipeline`` section)
and materializes per-worktree pipeline scripts under ``/lustre/work/sweeden/agent-*``.

Usage::

    python -m paperbench.scripts.generate_rogii_pipelines --all
    python -m paperbench.scripts.generate_rogii_pipelines --all --submit
    python -m paperbench.scripts.generate_rogii_pipelines --variant typewell_gr_alignment
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from paperbench.trace_pipeline.frontier_config import (
    RogiiPipelineConfig,
    RogiiVariantConfig,
    load_rogii_pipeline_config,
)

FRONTIER_PAPERBENCH = Path(__file__).resolve().parents[2]
SUBMIT_WRAPPER_TEMPLATE = """#!/usr/bin/env bash
# Auto-generated from frontier.yaml — submit phases 01–06 for {slug}.
# Worktree: {worktree}
set -euo pipefail
export AGENT_TRACING_ROOT="{agent_tracing_root}"
export ROGII_ROOT="{rogii_root}"
export VARIANT="{slug}"
export TRACE_VARIANT="{slug}"
exec "${{AGENT_TRACING_ROOT}}/examples/rogii/hpcc/submit_trace_pipeline.sh" "$@"
"""

RUN_PIPELINE_TEMPLATE = """#!/usr/bin/env bash
# Auto-generated from frontier.yaml — login-node dry-run gate for {slug}.
set -euo pipefail
export ROGII_ROOT="{agent_tracing_root}"
export AGENT_TRACING_ROOT="{agent_tracing_root}"
cd /lustre/work/sweeden/frontier-evals/project/paperbench
uv run python -m paperbench.trace_pipeline.orchestrator \\
  --variant {slug} \\
  --trace-path "{trace_csv}" \\
  --dry-run
uv run python -m paperbench.scripts.implement_agent_tracing --validate-traces
"""

SUBMIT_ALL_TEMPLATE = """#!/usr/bin/env bash
# Auto-generated: submit all six Rogii variant pipelines (one active job per variant).
set -euo pipefail
ROOT="{frontier_root}"
GENERATED="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
SUBMIT="${{1:-}}"
for script in "${{GENERATED}}"/submit_*.sh; do
  base="$(basename "${{script}}")"
  [[ "${{base}}" == submit_all_variants.sh ]] && continue
  tag="${{base#submit_}}"
  tag="${{tag%.sh}}"
  if squeue -u "${{USER}}" -o "%.30j" 2>/dev/null | grep -qE "trace_${{tag}}|trace_${{tag}}_p"; then
    echo "SKIP ${{script}}: job already queued/running"
    continue
  fi
  echo "=== ${{script}} ==="
  if [[ "${{SUBMIT}}" == "--submit" ]]; then
    bash "${{script}}"
  else
    DRY_RUN=1 bash "${{script}}"
  fi
done
echo "Done. Pass --submit to enqueue Slurm jobs."
"""


def _symlink_hpcc(cfg: RogiiPipelineConfig, worktree_root: Path) -> Path | None:
    """Symlink shared hpcc/ into a worktree if missing."""
    dest = worktree_root / "examples" / "rogii" / "hpcc"
    src = cfg.hpcc_source
    if not src.is_dir():
        raise FileNotFoundError(f"hpcc source missing: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() and dest.resolve() == src.resolve():
        return None
    if dest.is_dir() and not dest.is_symlink():
        return dest
    if dest.exists():
        dest.unlink()
    os.symlink(src.resolve(), dest)
    return dest


def _write_submit_wrapper(v: RogiiVariantConfig, cfg: RogiiPipelineConfig, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"submit_{v.slurm_job_tag.replace('trace_', '')}.sh"
    text = SUBMIT_WRAPPER_TEMPLATE.format(
        slug=v.slug,
        worktree=v.worktree,
        agent_tracing_root=v.agent_tracing_root,
        rogii_root=cfg.ml_code_root,
    )
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)
    return path


def _write_run_pipeline(v: RogiiVariantConfig) -> Path | None:
    if not v.variant_dir.is_dir():
        return None
    path = v.variant_dir / "run_pipeline.sh"
    path.write_text(
        RUN_PIPELINE_TEMPLATE.format(
            slug=v.slug,
            agent_tracing_root=v.agent_tracing_root,
            trace_csv=v.trace_csv,
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _sync_shared_from_primary(v: RogiiVariantConfig, cfg: RogiiPipelineConfig) -> bool:
    """Copy _shared/ from primary worktree into dedicated worktrees."""
    if v.worktree == cfg.primary_worktree:
        return False
    src = cfg.primary_root / "examples" / "rogii" / "traces" / "preprocessing" / "_shared"
    dst = v.agent_tracing_root / "examples" / "rogii" / "traces" / "preprocessing" / "_shared"
    if not src.is_dir():
        return False
    if dst.is_dir():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return True


def _write_manifest(cfg: RogiiPipelineConfig, generated: list[dict]) -> Path:
    manifest_dir = FRONTIER_PAPERBENCH / "data" / "rogii"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / "pipeline_manifest.json"
    payload = {
        "source": "frontier.yaml#rogii_pipeline",
        "ml_code_root": str(cfg.ml_code_root),
        "hpcc_source": str(cfg.hpcc_source),
        "phases": list(cfg.phases),
        "pipelines": generated,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _run_descriptors_and_papers(cfg: RogiiPipelineConfig) -> None:
    env = os.environ.copy()
    env["ROGII_ROOT"] = str(cfg.primary_root)
    subprocess.run(
        [sys.executable, "-m", "paperbench.scripts.sync_rogii_papers"],
        cwd=FRONTIER_PAPERBENCH,
        env=env,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "paperbench.scripts.write_experiment_descriptors",
            "--all-variants",
            "--rogii-root",
            str(cfg.primary_root),
        ],
        cwd=FRONTIER_PAPERBENCH,
        env=env,
        check=True,
    )


def _submit_variant(v: RogiiVariantConfig, cfg: RogiiPipelineConfig, *, dry_run: bool) -> None:
    if shutil.which("squeue") is None:
        raise RuntimeError("squeue not available")
    tag = v.slurm_job_tag
    check = subprocess.run(
        ["squeue", "-u", os.environ.get("USER", ""), "-o", "%.30j"],
        capture_output=True,
        text=True,
    )
    if tag in check.stdout or f"{tag}_p" in check.stdout:
        print(f"SKIP submit {v.slug}: {tag} already active")
        return
    env = os.environ.copy()
    env["AGENT_TRACING_ROOT"] = str(v.agent_tracing_root)
    env["ROGII_ROOT"] = str(cfg.ml_code_root)
    env["VARIANT"] = v.slug
    env["TRACE_VARIANT"] = v.slug
    if dry_run:
        env["DRY_RUN"] = "1"
    submit = v.agent_tracing_root / "examples" / "rogii" / "hpcc" / "submit_trace_pipeline.sh"
    if not submit.is_file():
        raise FileNotFoundError(submit)
    subprocess.run(["bash", str(submit)], cwd=v.agent_tracing_root, env=env, check=True)


def generate_variant(v: RogiiVariantConfig, cfg: RogiiPipelineConfig) -> dict:
    actions: list[str] = []
    hpcc = _symlink_hpcc(cfg, v.agent_tracing_root)
    if hpcc:
        actions.append(f"symlink hpcc -> {v.worktree}")

    if _sync_shared_from_primary(v, cfg):
        actions.append(f"sync _shared/ -> {v.worktree}")

    gen_dir = cfg.primary_root / "examples" / "rogii" / "generated"
    wrapper = _write_submit_wrapper(v, cfg, gen_dir)
    actions.append(f"wrote {wrapper.name}")

    run_p = _write_run_pipeline(v)
    if run_p:
        actions.append(f"wrote {run_p.relative_to(v.agent_tracing_root)}")

    return {
        "variant": v.slug,
        "worktree": v.worktree,
        "branch": v.branch,
        "slurm_job_tag": v.slurm_job_tag,
        "agent_tracing_root": str(v.agent_tracing_root),
        "variant_dir": str(v.variant_dir),
        "trace_csv": str(v.trace_csv),
        "submit_wrapper": str(wrapper),
        "trace_exists": v.trace_csv.is_file(),
        "actions": actions,
    }


def generate_unified_wrappers(cfg: RogiiPipelineConfig) -> list[dict]:
    """Submit wrappers for all variants under the unified agent-tracing checkout."""
    unified = cfg.sweeden_root / cfg.unified_worktree
    if not unified.is_dir():
        return []
    _symlink_hpcc(cfg, unified)
    gen_dir = unified / "examples" / "rogii" / "generated"
    rows: list[dict] = []
    for v in cfg.variants:
        uv = RogiiVariantConfig(
            slug=v.slug,
            worktree=cfg.unified_worktree,
            branch=v.branch,
            slurm_job_tag=v.slurm_job_tag,
            sweeden_root=cfg.sweeden_root,
        )
        wrapper = _write_submit_wrapper(uv, cfg, gen_dir)
        _write_run_pipeline(uv)
        rows.append(
            {
                "variant": v.slug,
                "worktree": cfg.unified_worktree,
                "submit_wrapper": str(wrapper),
                "agent_tracing_root": str(unified),
            }
        )
    return rows


def generate_all(
    cfg: RogiiPipelineConfig,
    *,
    variants: list[str] | None = None,
    sync_meta: bool = True,
) -> list[dict]:
    selected = cfg.variants
    if variants:
        slugs = set(variants)
        selected = tuple(v for v in cfg.variants if v.slug in slugs)

    if sync_meta:
        _run_descriptors_and_papers(cfg)

    generated: list[dict] = []
    for v in selected:
        generated.append(generate_variant(v, cfg))

    gen_dir = cfg.primary_root / "examples" / "rogii" / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    submit_all = gen_dir / "submit_all_variants.sh"
    submit_all.write_text(
        SUBMIT_ALL_TEMPLATE.format(frontier_root=cfg.sweeden_root.parent / "frontier-evals"),
        encoding="utf-8",
    )
    submit_all.chmod(0o755)

    manifest = _write_manifest(cfg, generated)
    print(f"Wrote manifest: {manifest}")
    print(f"Wrote submit-all: {submit_all}")
    return generated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier-yaml", type=Path, default=None)
    parser.add_argument("--all", action="store_true", help="Generate all six variants")
    parser.add_argument("--variant", action="append", metavar="SLUG")
    parser.add_argument("--no-sync-meta", action="store_true", help="Skip paper/descriptor sync")
    parser.add_argument("--submit", action="store_true", help="Submit Slurm pipelines (not dry-run)")
    parser.add_argument("--dry-run-submit", action="store_true", help="Print sbatch commands only")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args(argv)

    cfg = load_rogii_pipeline_config(args.frontier_yaml)
    if not args.all and not args.variant:
        parser.error("specify --all or --variant SLUG")

    slugs = args.variant if args.variant else None
    results = generate_all(cfg, variants=slugs, sync_meta=not args.no_sync_meta)

    for row in results:
        if not args.quiet:
            print(f"\n=== {row['variant']} @ {row['worktree']} ===")
            for act in row["actions"]:
                print(f"  {act}")
            if not row["trace_exists"]:
                print(f"  WARN: missing {row['trace_csv']}")

    unified = generate_unified_wrappers(cfg)
    if unified and not args.quiet:
        print(f"\n=== unified {cfg.unified_worktree} ({len(unified)} wrappers) ===")
        for row in unified:
            print(f"  {row['variant']} -> {row['submit_wrapper']}")

    if args.submit or args.dry_run_submit:
        for v in cfg.variants:
            if slugs and v.slug not in slugs:
                continue
            _submit_variant(v, cfg, dry_run=not args.submit)

    print(f"\nGenerated {len(results)} pipeline(s) from frontier.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
