from __future__ import annotations

from dataclasses import dataclass

from paperbench.chomsky.producer_consumer import CANONICAL_HEADERS

RESOURCE_ENVELOPE_COLUMNS: tuple[str, ...] = (
    "chomsky_type",
    "llm_model",
    "context_window_tokens",
    "context_policy",
    "long_term_memory",
    "ltm_growth_bound",
    "slurm_partition",
    "slurm_resources",
    "gpu_device",
)

EXTENDED_HEADERS: tuple[str, ...] = CANONICAL_HEADERS + RESOURCE_ENVELOPE_COLUMNS

ENVELOPE_TOKEN = "declare_envelope"
ENVELOPE_ROW_COUNT = len(CANONICAL_HEADERS)
ENVELOPE_ROW_START = 1  # 0-based index after header
ENVELOPE_ROW_END = ENVELOPE_ROW_START + ENVELOPE_ROW_COUNT  # exclusive

VALID_CHOMSKY_TYPES = frozenset({"Type-3", "Type-2", "Type-1", "Type-0"})
VALID_CONTEXT_POLICIES = frozenset({"halt", "truncate_middle", "rolling_window", "none", "—", ""})
VALID_LTM = frozenset(
    {
        "none",
        "transcript",
        "artifact_cache",
        "lustre_files",
        "vector_store",
        "fold_stack",
        "seed_stack",
        "oof_vectors",
        "residuals",
        "external_api",
        "adr_store",
        "markdown_files",
        "dag_stack",
        "seed_history",
    }
)
VALID_LTM_BOUNDS = frozenset({"O(1)", "O(n)", "O(log n)", "O(k)", "O(V+E)", "unbounded"})


@dataclass(frozen=True)
class AgentEnvelope:
    chomsky_type: str
    llm_model: str
    context_window_tokens: int
    context_policy: str
    long_term_memory: str
    ltm_growth_bound: str
    slurm_partition: str
    slurm_resources: str
    gpu_device: str

    def to_row_suffix(self) -> list[str]:
        return [
            self.chomsky_type,
            self.llm_model,
            str(self.context_window_tokens),
            self.context_policy,
            self.long_term_memory,
            self.ltm_growth_bound,
            self.slurm_partition,
            self.slurm_resources,
            self.gpu_device,
        ]


def _env(**kwargs: str | int) -> AgentEnvelope:
    return AgentEnvelope(
        chomsky_type=str(kwargs["chomsky_type"]),
        llm_model=str(kwargs.get("llm_model", "none")),
        context_window_tokens=int(kwargs.get("context_window_tokens", 0)),
        context_policy=str(kwargs.get("context_policy", "none")),
        long_term_memory=str(kwargs.get("long_term_memory", "none")),
        ltm_growth_bound=str(kwargs.get("ltm_growth_bound", "O(1)")),
        slurm_partition=str(kwargs.get("slurm_partition", "matador")),
        slurm_resources=str(kwargs["slurm_resources"]),
        gpu_device=str(kwargs.get("gpu_device", "none")),
    )


DEFAULT_AGENT_ENVELOPES: dict[str, AgentEnvelope] = {
    "data_downloader": _env(
        chomsky_type="Type-0",
        long_term_memory="lustre_files",
        ltm_growth_bound="unbounded",
        slurm_resources="cpus=8,mem=32G,gpu=0,time=02:00:00",
    ),
    "schema-sentinel": _env(
        chomsky_type="Type-3",
        context_policy="halt",
        slurm_resources="cpus=2,mem=4G,gpu=0,time=00:30:00",
    ),
    "eda_profiler": _env(
        chomsky_type="Type-1",
        long_term_memory="transcript",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=4,mem=16G,gpu=0,time=01:00:00",
    ),
    "well_group_detector": _env(
        chomsky_type="Type-1",
        long_term_memory="transcript",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=2,mem=8G,gpu=0,time=00:30:00",
    ),
    "target_diagnostician": _env(
        chomsky_type="Type-1",
        long_term_memory="transcript",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=2,mem=8G,gpu=0,time=00:30:00",
    ),
    "feature_engineer": _env(
        chomsky_type="Type-1",
        long_term_memory="artifact_cache",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=4,mem=16G,gpu=0,time=01:00:00",
    ),
    "preprocessor": _env(
        chomsky_type="Type-1",
        long_term_memory="artifact_cache",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=4,mem=16G,gpu=0,time=01:00:00",
    ),
    "cv_orchestrator": _env(
        chomsky_type="Type-2",
        long_term_memory="fold_stack",
        ltm_growth_bound="O(k)",
        slurm_resources="cpus=4,mem=16G,gpu=0,time=02:00:00",
    ),
    "model_trainer": _env(
        chomsky_type="Type-0",
        long_term_memory="artifact_cache",
        ltm_growth_bound="unbounded",
        slurm_resources="cpus=8,mem=100G,gpu=1,time=04:00:00",
        gpu_device="cuda:0",
    ),
    "model_ensembler": _env(
        chomsky_type="Type-2",
        long_term_memory="seed_stack",
        ltm_growth_bound="O(k)",
        slurm_resources="cpus=8,mem=64G,gpu=1,time=02:00:00",
        gpu_device="lightgbm_gpu",
    ),
    "predictor": _env(
        chomsky_type="Type-1",
        long_term_memory="fold_stack",
        ltm_growth_bound="O(k)",
        slurm_resources="cpus=4,mem=32G,gpu=1,time=01:00:00",
        gpu_device="cuda:0",
    ),
    "oof_evaluator": _env(
        chomsky_type="Type-1",
        long_term_memory="oof_vectors",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=2,mem=8G,gpu=0,time=00:30:00",
    ),
    "error_analyzer": _env(
        chomsky_type="Type-1",
        long_term_memory="residuals",
        ltm_growth_bound="O(n)",
        slurm_resources="cpus=2,mem=8G,gpu=0,time=00:30:00",
    ),
    "submission_formatter": _env(
        chomsky_type="Type-3",
        context_policy="halt",
        slurm_resources="cpus=1,mem=4G,gpu=0,time=00:15:00",
    ),
    "submission_validator": _env(
        chomsky_type="Type-3",
        context_policy="halt",
        slurm_resources="cpus=1,mem=4G,gpu=0,time=00:15:00",
    ),
    "kaggle_submitter": _env(
        chomsky_type="Type-0",
        long_term_memory="external_api",
        ltm_growth_bound="unbounded",
        slurm_resources="cpus=1,mem=4G,gpu=0,time=00:30:00",
    ),
    "seed-control-officer": _env(
        chomsky_type="Type-3",
        context_policy="halt",
        long_term_memory="seed_history",
        slurm_resources="cpus=1,mem=2G,gpu=0,time=00:05:00",
    ),
    "experiment-design-architect": _env(
        chomsky_type="Type-0",
        llm_model="granite4:3b",
        context_window_tokens=8192,
        context_policy="rolling_window",
        long_term_memory="adr_store",
        ltm_growth_bound="unbounded",
        slurm_resources="cpus=8,mem=32G,gpu=1,time=48:00:00",
        gpu_device="cuda:0",
    ),
    "architecture-decision-recorder": _env(
        chomsky_type="Type-0",
        llm_model="granite4:3b",
        context_window_tokens=8192,
        context_policy="truncate_middle",
        long_term_memory="markdown_files",
        ltm_growth_bound="unbounded",
        slurm_resources="cpus=8,mem=32G,gpu=1,time=48:00:00",
        gpu_device="cuda:0",
    ),
    "dependency-graph-orchestrator": _env(
        chomsky_type="Type-2",
        long_term_memory="dag_stack",
        ltm_growth_bound="O(V+E)",
        slurm_resources="cpus=2,mem=4G,gpu=0,time=00:30:00",
    ),
}

VARIANT_ENVELOPE_OVERRIDES: dict[str, dict[str, AgentEnvelope]] = {
    "parallel_multiwell_loader": {
        "data_downloader": _env(
            chomsky_type="Type-0",
            long_term_memory="lustre_files",
            ltm_growth_bound="unbounded",
            slurm_resources="cpus=16,mem=64G,gpu=0,time=02:00:00",
        ),
    },
    "typewell_gr_alignment": {
        "feature_engineer": _env(
            chomsky_type="Type-1",
            long_term_memory="artifact_cache",
            ltm_growth_bound="O(n)",
            slurm_resources="cpus=8,mem=32G,gpu=0,time=01:00:00",
        ),
    },
    "formation_plane_spatial": {
        "feature_engineer": _env(
            chomsky_type="Type-1",
            long_term_memory="artifact_cache",
            ltm_growth_bound="O(n)",
            slurm_resources="cpus=8,mem=32G,gpu=0,time=01:00:00",
        ),
    },
    "ps_point_leakage_aware": {
        "target_diagnostician": _env(
            chomsky_type="Type-1",
            long_term_memory="transcript",
            ltm_growth_bound="O(n)",
            slurm_resources="cpus=4,mem=16G,gpu=0,time=00:30:00",
        ),
    },
}


def envelopes_for_variant(variant: str | None) -> dict[str, AgentEnvelope]:
    out = dict(DEFAULT_AGENT_ENVELOPES)
    if variant and variant in VARIANT_ENVELOPE_OVERRIDES:
        out.update(VARIANT_ENVELOPE_OVERRIDES[variant])
    return out


COMPUTING_RESOURCE_EVAL_TOKENS = (
    "evaluate_computing_resources_chomsky_rubric",
    "validate_resource_bounds_per_chomsky_class",
    "validate_slurm_envelope_vs_hpcc_scripts",
)


def validate_resource_envelope_rows(rows: list[list[str]]) -> list[str]:
    """Validate declare_envelope block (rows 2-21) and resource column values."""
    errors: list[str] = []
    if not rows:
        return errors
    header = [h.strip() for h in rows[0]]
    if len(header) != len(EXTENDED_HEADERS):
        return errors

    resource_start = len(CANONICAL_HEADERS)
    for i, agent in enumerate(CANONICAL_HEADERS):
        row_idx = ENVELOPE_ROW_START + i
        if row_idx >= len(rows):
            errors.append(f"missing envelope row for {agent}")
            continue
        row = rows[row_idx]
        if len(row) < len(EXTENDED_HEADERS):
            errors.append(f"envelope row {row_idx + 1} for {agent}: column count too short")
            continue
        if row[i].strip() != ENVELOPE_TOKEN:
            errors.append(f"envelope row {row_idx + 1}: expected {ENVELOPE_TOKEN!r} in {agent}")
        swim_others = [row[j].strip() for j in range(len(CANONICAL_HEADERS)) if j != i]
        if any(swim_others):
            errors.append(f"envelope row {row_idx + 1}: non-target swim lanes must be empty")

        res = [c.strip() for c in row[resource_start : resource_start + len(RESOURCE_ENVELOPE_COLUMNS)]]
        if len(res) != len(RESOURCE_ENVELOPE_COLUMNS):
            errors.append(f"envelope row {row_idx + 1}: incomplete resource columns")
            continue
        chomsky_type, llm_model, ctx_tokens, ctx_policy, ltm, ltm_bound, partition, slurm, gpu = res
        if chomsky_type not in VALID_CHOMSKY_TYPES:
            errors.append(f"envelope row {row_idx + 1}: invalid chomsky_type {chomsky_type!r}")
        if ctx_policy not in VALID_CONTEXT_POLICIES:
            errors.append(f"envelope row {row_idx + 1}: invalid context_policy {ctx_policy!r}")
        if ltm not in VALID_LTM:
            errors.append(f"envelope row {row_idx + 1}: invalid long_term_memory {ltm!r}")
        if ltm_bound not in VALID_LTM_BOUNDS:
            errors.append(f"envelope row {row_idx + 1}: invalid ltm_growth_bound {ltm_bound!r}")
        if not slurm:
            errors.append(f"envelope row {row_idx + 1}: slurm_resources required")
        if chomsky_type in {"Type-3", "Type-2"} and llm_model not in ("none", ""):
            errors.append(f"envelope row {row_idx + 1}: {agent} should not declare LLM for {chomsky_type}")
        if chomsky_type == "Type-0" and llm_model not in ("none", "") and int(ctx_tokens or 0) <= 0:
            errors.append(f"envelope row {row_idx + 1}: Type-0 LLM agent {agent} needs context_window_tokens > 0")

    return errors
