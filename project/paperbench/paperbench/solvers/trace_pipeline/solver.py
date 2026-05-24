from __future__ import annotations

import json
import time
from pathlib import Path

import structlog
from typing_extensions import override

import chz
from nanoeval.solvers.computer_tasks.code_execution_interface import ComputerInterface
from paperbench.nano.structs import AgentOutput
from paperbench.nano.task import PBTask
from paperbench.solvers.base import BasePBSolver
from paperbench.solvers.utils import check_for_existing_run

logger = structlog.stdlib.get_logger(component=__name__)

from paperbench.trace_pipeline.paths import resolve_rogii_root, resolve_trace_path


@chz.chz
class TracePipelineSolver(BasePBSolver):
    variant: str = chz.field(default="baseline_column_transformer")

    @override
    def shortname(self) -> str:
        return f"trace-{self.variant}"

    async def _run_agent(self, computer: ComputerInterface, task: PBTask) -> AgentOutput:
        agent_output = await check_for_existing_run(task)
        if agent_output:
            return agent_output

        start = time.time()
        rogii_root = resolve_rogii_root()
        trace = resolve_trace_path(self.variant)
        script = (
            f"cd /lustre/work/sweeden/frontier-evals/project/paperbench && "
            f"ROGII_ROOT={rogii_root} uv run python -m paperbench.trace_pipeline.orchestrator "
            f"--variant {self.variant} --trace-path {trace} --dry-run"
        )
        await computer.send_shell_command(script)
        repro = (
            "#!/bin/bash\n"
            "set -euo pipefail\n"
            f"cd /lustre/work/sweeden/frontier-evals/project/paperbench\n"
            f"ROGII_ROOT={rogii_root} uv run python -m paperbench.trace_pipeline.orchestrator --variant {self.variant} --dry-run\n"
            f"uv run python -m paperbench.scripts.implement_agent_tracing --validate-traces\n"
        )
        await computer.upload(repro.encode(), "/home/submission/reproduce.sh")

        return AgentOutput(
            run_id=task.run_id,
            time_start=start,
            time_end=time.time(),
            error_msg=None,
            runtime_in_seconds=time.time() - start,
            status_exists=True,
        )
