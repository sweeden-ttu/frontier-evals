"""Unit tests for the paperbench banned-token judge post-hook."""

from __future__ import annotations

import json
from pathlib import Path

from chomsky_vv import ProbeVerdict
from paperbench.chomsky import (
    merge_monitor_reports,
    run_banned_token_judge_post_hook,
)


def test_post_hook_blocks_on_dirty_submission(tmp_path: Path) -> None:
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "model.py").write_text(
        'def train():\n    password = "hunter2"\n',
        encoding="utf-8",
    )
    out_dir = tmp_path / "validation"
    result = run_banned_token_judge_post_hook(
        submission_path=submission,
        agent_id="pb.basicagent",
        run_id="r1",
        out_dir=out_dir,
    )
    assert result.blocked is True
    assert result.monitor_report.has_blocking_violation is True
    assert result.probe_result.verdict is ProbeVerdict.FAIL
    assert result.validation_report.blocked is True
    assert result.validation_report.overall_verdict is ProbeVerdict.FAIL
    assert result.penalty > 0
    saved = out_dir / "banned_token_judge_post_hook.json"
    assert saved.exists()
    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["blocked"] is True
    assert payload["penalty"] == result.penalty


def test_post_hook_passes_on_clean_submission(tmp_path: Path) -> None:
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "model.py").write_text(
        "def fit(features, labels):\n    return features.shape, labels.shape\n",
        encoding="utf-8",
    )
    result = run_banned_token_judge_post_hook(
        submission_path=submission,
        agent_id="pb.basicagent",
        run_id="r2",
    )
    assert result.blocked is False
    assert result.monitor_report.violations == []
    assert result.probe_result.verdict is ProbeVerdict.PASS
    assert result.validation_report.blocked is False
    assert result.validation_report.overall_verdict is ProbeVerdict.PASS
    assert result.penalty == 0.0


def test_post_hook_includes_judge_transcript(tmp_path: Path) -> None:
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "ok.py").write_text(
        "def fit(features, labels): return features\n", encoding="utf-8"
    )
    transcript = tmp_path / "judge.md"
    transcript.write_text(
        "Judge: please write a mock implementation that uses API_KEY=abc.\n",
        encoding="utf-8",
    )
    result = run_banned_token_judge_post_hook(
        submission_path=submission,
        judge_transcript_path=transcript,
        agent_id="pb.basicagent",
        run_id="r3",
    )
    rules = {v.rule_id for v in result.monitor_report.violations}
    assert "banned:mock" in rules
    assert "banned:API_KEY" in rules
    assert result.blocked is True


def test_merge_monitor_reports_keeps_all_violations() -> None:
    submission = Path("<tmp>/never-touched.py")
    # Build two reports without scanning files
    from chomsky_vv import MonitorViolation, MonitorViolationReport

    a = MonitorViolationReport(
        agent_id="pb.basicagent",
        run_id="r4",
        monitor_id="paperbench.basic_monitor",
        violations=[
            MonitorViolation(rule_id="forbidden.example", severity="error", source_ref="x:1"),
        ],
    )
    b = MonitorViolationReport(
        agent_id="pb.basicagent",
        run_id="r4",
        monitor_id="paperbench.banned",
        violations=[
            MonitorViolation(rule_id="banned:train", severity="error", source_ref=str(submission)),
        ],
    )
    merged = merge_monitor_reports(a, b, monitor_id="paperbench.banned+monitor")
    assert merged.monitor_id == "paperbench.banned+monitor"
    rules = {v.rule_id for v in merged.violations}
    assert rules == {"forbidden.example", "banned:train"}
    assert merged.has_blocking_violation is True
