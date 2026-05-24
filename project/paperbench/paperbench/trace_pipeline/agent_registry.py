from __future__ import annotations

import importlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from paperbench.chomsky.producer_consumer import CANONICAL_HEADERS
from paperbench.trace_pipeline.paths import resolve_rogii_root

ROGII_ROOT = resolve_rogii_root()


@dataclass
class AgentRegistry:
    """Maps swim-lane column names to callables / rogii pipeline agents."""

    handlers: dict[str, Callable[..., Any]] = field(default_factory=dict)

    @classmethod
    def from_rogii_pipeline(cls) -> AgentRegistry:
        reg = cls()
        try:
            mod = importlib.import_module("pipeline.agents")
        except ImportError:
            return reg
        for name in CANONICAL_HEADERS:
            slug = name.replace("-", "_")
            for attr in dir(mod):
                if attr.lower().replace("_", "-") == name or attr == "".join(p.title() for p in name.split("-")):
                    reg.handlers[name] = getattr(mod, attr)
        reg.handlers["schema-sentinel"] = getattr(mod, "SchemaSentinel", None)
        reg.handlers["submission_validator"] = getattr(mod, "SubmissionEnvelopeValidator", None)
        reg.handlers["type3_consumer"] = getattr(mod, "Type3ConsumerGate", None)
        return reg

    def invoke_token(self, lane: str, token: str, *, dry_run: bool = False) -> dict[str, Any]:
        if dry_run:
            return {"lane": lane, "token": token, "status": "dry_run"}
        if token.startswith("cd ") or "kaggle" in token or "sbatch" in token or token.startswith("python "):
            if dry_run:
                return {"lane": lane, "token": token, "status": "skipped_cli"}
            proc = subprocess.run(token, shell=True, cwd=ROGII_ROOT, capture_output=True, text=True)
            return {
                "lane": lane,
                "token": token,
                "status": "pass" if proc.returncode == 0 else "fail",
                "exit_code": proc.returncode,
            }
        return {"lane": lane, "token": token, "status": "noop"}
