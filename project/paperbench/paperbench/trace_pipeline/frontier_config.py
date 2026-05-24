"""Load Rogii pipeline / worktree configuration from frontier.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

_FRONTIER_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_FRONTIER_YAML = _FRONTIER_ROOT / "frontier.yaml"


@dataclass(frozen=True)
class RogiiVariantConfig:
    slug: str
    worktree: str
    branch: str
    slurm_job_tag: str
    sweeden_root: Path

    @property
    def worktree_root(self) -> Path:
        return self.sweeden_root / self.worktree

    @property
    def agent_tracing_root(self) -> Path:
        return self.worktree_root

    @property
    def variant_dir(self) -> Path:
        return (
            self.agent_tracing_root
            / "examples"
            / "rogii"
            / "traces"
            / "preprocessing"
            / self.slug
        )

    @property
    def trace_csv(self) -> Path:
        return self.variant_dir / "trace_language.csv"


@dataclass(frozen=True)
class RogiiPipelineConfig:
    sweeden_root: Path
    primary_worktree: str
    unified_worktree: str
    ml_code_root: Path
    hpcc_source: Path
    conda_prefix: Path
    slurm_partition: str
    phases: tuple[str, ...]
    variants: tuple[RogiiVariantConfig, ...]

    @property
    def primary_root(self) -> Path:
        return self.sweeden_root / self.primary_worktree

    def variant(self, slug: str) -> RogiiVariantConfig:
        for v in self.variants:
            if v.slug == slug:
                return v
        raise KeyError(slug)

    def worktree_roots(self) -> list[Path]:
        roots: list[Path] = []
        seen: set[Path] = set()
        for v in self.variants:
            root = v.agent_tracing_root
            if root not in seen:
                seen.add(root)
                roots.append(root)
        unified = self.sweeden_root / self.unified_worktree
        if unified.is_dir() and unified not in seen:
            roots.append(unified)
        return roots


def load_frontier_yaml(path: Path | None = None) -> dict:
    yaml_path = path or Path(os.environ.get("FRONTIER_YAML", _DEFAULT_FRONTIER_YAML))
    if not yaml_path.is_file():
        raise FileNotFoundError(f"frontier.yaml not found: {yaml_path}")
    return yaml.load(yaml_path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader)


def load_rogii_pipeline_config(path: Path | None = None) -> RogiiPipelineConfig:
    raw = load_frontier_yaml(path)
    section = raw.get("rogii_pipeline")
    if not section:
        raise ValueError("frontier.yaml missing rogii_pipeline section")

    sweeden = Path(section["sweeden_root"])
    variants = tuple(
        RogiiVariantConfig(
            slug=v["slug"],
            worktree=v["worktree"],
            branch=v["branch"],
            slurm_job_tag=v["slurm_job_tag"],
            sweeden_root=sweeden,
        )
        for v in section["variants"]
    )
    return RogiiPipelineConfig(
        sweeden_root=sweeden,
        primary_worktree=section["primary_worktree"],
        unified_worktree=section.get("unified_worktree", "agent-tracing"),
        ml_code_root=Path(section["ml_code_root"]),
        hpcc_source=Path(section["hpcc_source"]),
        conda_prefix=Path(section["conda_prefix"]),
        slurm_partition=section.get("slurm_partition", "matador"),
        phases=tuple(section["phases"]),
        variants=variants,
    )


def discover_agent_worktrees(sweeden_root: Path | None = None) -> list[Path]:
    root = sweeden_root or Path("/lustre/work/sweeden")
    return sorted(
        p for p in root.glob("agent-tracing*") if p.is_dir() and (p / "examples").is_dir()
    )
