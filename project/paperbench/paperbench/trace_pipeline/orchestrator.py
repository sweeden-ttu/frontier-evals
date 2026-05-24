from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from paperbench.chomsky.trace_csv import validate_trace_language_csv
from paperbench.trace_pipeline.agent_registry import AgentRegistry, ROGII_ROOT


class TracePipelineOrchestrator:
    def __init__(
        self,
        *,
        variant: str,
        trace_path: Path | None = None,
        rogii_root: Path = ROGII_ROOT,
    ) -> None:
        self.variant = variant
        self.rogii_root = rogii_root
        if trace_path is None:
            trace_path = (
                rogii_root
                / "traces"
                / "preprocessing"
                / variant
                / "trace_language.csv"
            )
        self.trace_path = trace_path
        self.registry = AgentRegistry.from_rogii_pipeline()

    def load_rows(self) -> list[list[str]]:
        with self.trace_path.open(newline="", encoding="utf-8") as f:
            return list(csv.reader(f))

    def run(self, *, dry_run: bool = True) -> list[dict]:
        report = validate_trace_language_csv(self.trace_path, require_canonical_header=False)
        if not report.valid:
            raise RuntimeError(f"Invalid trace: {report.errors}")

        rows = self.load_rows()
        header = rows[0]
        results: list[dict] = []
        for row in rows[1:]:
            for col_idx, cell in enumerate(row):
                cell = cell.strip()
                if not cell or col_idx >= len(header):
                    continue
                lane = header[col_idx]
                results.append(self.registry.invoke_token(lane, cell, dry_run=dry_run))
        return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Rogii trace pipeline orchestrator")
    parser.add_argument("--variant", required=True)
    parser.add_argument("--trace-path", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="Run CLI cells (not dry-run)")
    args = parser.parse_args(argv)
    orch = TracePipelineOrchestrator(variant=args.variant, trace_path=args.trace_path)
    dry = not args.execute
    results = orch.run(dry_run=dry)
    print(f"variant={args.variant} steps={len(results)} dry_run={dry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
