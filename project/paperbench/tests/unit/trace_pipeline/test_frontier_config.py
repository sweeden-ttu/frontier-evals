"""Tests for frontier.yaml Rogii pipeline config."""

from __future__ import annotations

from pathlib import Path

from paperbench.trace_pipeline.frontier_config import (
    discover_agent_worktrees,
    load_rogii_pipeline_config,
)


def test_load_rogii_pipeline_config():
    cfg = load_rogii_pipeline_config()
    assert len(cfg.variants) == 6
    assert cfg.primary_worktree == "agent-tracing-trace-baseline"
    slugs = {v.slug for v in cfg.variants}
    assert "typewell_gr_alignment" in slugs
    assert "formation_plane_spatial" in slugs


def test_variant_worktree_paths():
    cfg = load_rogii_pipeline_config()
    v = cfg.variant("typewell_gr_alignment")
    assert v.worktree == "agent-tracing-trace-typewell"
    assert v.worktree_root == Path("/lustre/work/sweeden/agent-tracing-trace-typewell")


def test_discover_agent_worktrees():
    roots = discover_agent_worktrees()
    names = {p.name for p in roots}
    assert "agent-tracing-trace-baseline" in names
