"""Experiment descriptors: scientific paper base + trace_language.csv agent layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paperbench.trace_pipeline.paper_registry import paper_file_for_descriptor
from paperbench.trace_pipeline.paths import resolve_rogii_root

TRACE_THEORY_PAPER: dict[str, Any] = {
    "paperbench_id": "agent-tracing",
    "title": "Agentic Programming as Formal Automata: A Chomsky-Hierarchy View of Tool-Using LLM Agents",
    "authors": "Scott Weeden",
    "bundle_path": "data/papers/agent-tracing",
    "role": "trace_language_audit_and_agent_implementation",
}

# Primary method/domain paper per variant (drives ablation hypotheses).
PEDREGOSA2011_SKLEARN: dict[str, Any] = {
    "id": "pedregosa2011_sklearn",
    "role": "preprocessing_experiment_descriptor",
    "title": "Scikit-learn: Machine Learning in Python",
    "authors": "Pedregosa, Varoquaux, Gramfort, Michel, Thirion, Grisel, Blondel, Prettenhofer, Weiss, Dubourg, Vanderplas, Passos, Cournapeau, Brucher, Perrot, Duchesnay",
    "short_authors": "Pedregosa et al.",
    "year": 2011,
    "venue": "JMLR",
    "doi": "10.5555/1953048.2029494",
    "url": "https://jmlr.org/papers/v12/pedregosa11a.html",
    "claims": [
        "ColumnTransformer applies disjoint transformers to heterogeneous column blocks.",
        "Pipeline compose chains preprocessing and estimator for leak-safe CV.",
        "numeric_scaler ablation (standard vs robust) maps to sklearn preprocessor choice.",
    ],
    "ablation_sections": ["§2 unified API", "ColumnTransformer / Pipeline compose"],
    "trace_tokens": [
        "build_numeric_pipeline",
        "build_lowcard_pipeline",
        "build_highcard_pipeline",
        "assemble_column_transformer",
    ],
}

KE2017_LIGHTGBM: dict[str, Any] = {
    "id": "ke2017_lightgbm",
    "role": "model_experiment_descriptor",
    "title": "LightGBM: A Highly Efficient Gradient Boosting Decision Tree",
    "authors": "Ke, Meng, Finley, Wang, Chen, Ma, Ye, Liu",
    "short_authors": "Ke et al.",
    "year": 2017,
    "venue": "NeurIPS",
    "doi": "10.5555/3294996.3295074",
    "url": "https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree",
    "claims": [
        "Histogram-based GBDT improves tabular regression speed and accuracy vs level-wise boosting.",
        "Leaf-wise growth with regularization supports strong baselines on heterogeneous numeric features.",
        "Pairs with heterogeneous column preprocessing (ColumnTransformer) on tabular well-log features.",
    ],
    "ablation_sections": ["§3 histogram algorithm", "§4 experiments on dense numeric features"],
    "trace_tokens": [
        "set_objective_regression",
        "set_metric_rmse",
        "log_best_iteration",
        "train_with_seed_42",
    ],
}

VARIANT_BASE_PAPERS: dict[str, dict[str, Any]] = {
    "baseline_column_transformer": {
        **KE2017_LIGHTGBM,
        "base_papers": [KE2017_LIGHTGBM, PEDREGOSA2011_SKLEARN],
        "trace_theory_sections": ["sec/2 agent schemata", "sec/4 evaluation audit protocol"],
    },
    "typewell_gr_alignment": {
        "title": "Dynamic Programming Algorithm Optimization for Spoken Word Recognition",
        "authors": "Sakoe, Chiba",
        "year": 1978,
        "venue": "IEEE Trans. Acoustics, Speech, and Signal Processing",
        "doi": "10.1109/TASSP.1978.1163055",
        "url": "https://ieeexplore.ieee.org/document/1163055",
        "claims": [
            "DTW aligns sequences with local warping—applicable to depth-indexed GR/typewell curves.",
            "Interpolation choice (linear vs PCHIP) changes tie-point smoothness and physics baseline RMSE.",
            "Typewell alignment is an inductive bias ablation: off vs on tests geologic transfer value.",
        ],
        "ablation_sections": ["§2 warping path", "§3 band constraints"],
        "supporting": [
            {
                "title": "The Geological Interpretation of Well Logs",
                "authors": "Rider, Kennedy",
                "year": 2011,
                "venue": "Whittles Publishing",
                "role": "Typewell / gamma-ray correlation domain vocabulary",
            }
        ],
        "trace_theory_sections": ["sec/3 Type-2 stack", "sec/7 R&D Bayesian loop"],
    },
    "ps_point_leakage_aware": {
        "title": "Leakage in Data Mining: Formulation, Detection, and Avoidance",
        "authors": "Kaufman, Rosset, Perlich, Stitelman",
        "year": 2012,
        "venue": "ACM TKDD",
        "doi": "10.1145/2382575.2382577",
        "url": "https://doi.org/10.1145/2382575.2382577",
        "claims": [
            "Train-test leakage inflates offline metrics; evaluation masks must match deployment horizon.",
            "Post-perforation-start (PS) RMSE is the competition-relevant subset—full-well eval is optimistic.",
            "Strict vs lenient TVT input audits are ablatable governance gates (Type-3 consumers).",
        ],
        "ablation_sections": ["§3 leakage taxonomy", "§5 detection strategies"],
        "supporting": [],
        "trace_theory_sections": ["sec/4 audit protocol", "sec/5 limitations"],
    },
    "robust_scale_log1p": {
        "title": "Robust Statistics: The Approach Based on Influence Functions",
        "authors": "Hampel, Ronchetti, Rousseuw, Stahel",
        "year": 1986,
        "venue": "Wiley",
        "doi": "10.1002/9781118186435",
        "url": "https://onlinelibrary.wiley.com/doi/book/10.1002/9781118186435",
        "claims": [
            "Robust location/scale estimators reduce outlier sensitivity vs ordinary standardization.",
            "log1p target transform stabilizes skewed well-log regression residuals.",
            "Inverse transform at predict time is an ablatable factor coupling train and inference stacks.",
        ],
        "ablation_sections": ["Ch. 2 influence functions", "Ch. 5 M-estimators"],
        "supporting": [
            {
                "title": "Scikit-learn: Machine Learning in Python",
                "authors": "Pedregosa et al.",
                "year": 2011,
                "venue": "JMLR",
                "role": "RobustScaler implementation reference",
            }
        ],
        "trace_theory_sections": ["sec/3 Type-1 linear transcript"],
    },
    "parallel_multiwell_loader": {
        "title": "Dask: Parallel Computation with Blocked algorithms and Task Scheduling",
        "authors": "Rocklin",
        "year": 2015,
        "venue": "SciPy proceedings",
        "url": "https://conference.scipy.org/proceedings/scipy2015/matthew_rocklin.html",
        "claims": [
            "Parallel blocked IO scales multi-well CSV ingestion beyond single-threaded loaders.",
            "Worker count and on-disk cache are ablatable throughput–memory tradeoffs.",
            "Geology surface columns add Type-1 feature materialization cost testable via on/off ablation.",
        ],
        "ablation_sections": ["§2 task graph", "§3 scheduling"],
        "supporting": [],
        "trace_theory_sections": ["sec/7 Bayesian loop", "sec/4 evaluation audit"],
    },
    "formation_plane_spatial": {
        "title": "Nearest Neighbor Pattern Classification",
        "authors": "Cover, Hart",
        "year": 1967,
        "venue": "IEEE Trans. Information Theory",
        "doi": "10.1109/TIT.1967.1053964",
        "url": "https://ieeexplore.ieee.org/document/1053964",
        "claims": [
            "k-NN risk bounds motivate formation-label propagation from spatial neighbors in TVD/MD space.",
            "Drilling geometry features encode directional survey context for plane-aware lithology.",
            "Formation plane fit (off/on) ablates explicit structural surface vs pure neighbor voting.",
        ],
        "ablation_sections": ["§1 k-NN error bounds", "§2 finite-sample behavior"],
        "supporting": [
            {
                "title": "A Two-Dimensional Interpolation Function for Irregularly-Spaced Data",
                "authors": "Shepard",
                "year": 1968,
                "venue": "ACM",
                "role": "Formation surface / plane interpolation analogue",
            }
        ],
        "trace_theory_sections": ["sec/3 Type-0 envelope"],
    },
}

VARIANT_APPROACHES: dict[str, str] = {
    "baseline_column_transformer": "ColumnTransformer + LightGBM baseline",
    "typewell_gr_alignment": "GR/typewell alignment features",
    "ps_point_leakage_aware": "PS-point detection + post-PS RMSE mask",
    "robust_scale_log1p": "RobustScaler + log1p target",
    "parallel_multiwell_loader": "Parallel IO + geology surfaces",
    "formation_plane_spatial": "Drilling geometry + formation KNN",
}


def variant_dir(variant: str, *, rogii_root: Path | None = None) -> Path:
    root = rogii_root or resolve_rogii_root()
    return root / "traces" / "preprocessing" / variant


def build_experiment_descriptor(
    variant: str,
    *,
    rogii_root: Path | None = None,
    ablation_factors: list[dict] | None = None,
) -> dict[str, Any]:
    """Join base scientific paper, ablation plan, and trace_language.csv paths."""
    if variant not in VARIANT_BASE_PAPERS:
        raise KeyError(f"unknown variant: {variant}")

    vdir = variant_dir(variant, rogii_root=rogii_root)
    base = VARIANT_BASE_PAPERS[variant]
    rel_trace = f"traces/preprocessing/{variant}/trace_language.csv"

    base_papers = base.get("base_papers")
    if base_papers:
        authors_years = ", ".join(
            f"{p.get('short_authors', p['authors'])} ({p['year']})" for p in base_papers
        )
        hypothesis = (
            f"{VARIANT_APPROACHES[variant]} improves competition RMSE (post-PS) vs shared baseline "
            f"under nested GroupKFold, as motivated by {authors_years}."
        )
    else:
        hypothesis = (
            f"{VARIANT_APPROACHES[variant]} improves competition RMSE (post-PS) vs shared baseline "
            f"under nested GroupKFold, as motivated by {base['authors']} ({base['year']})."
        )

    descriptor: dict[str, Any] = {
        "variant": variant,
        "approach": VARIANT_APPROACHES[variant],
        "branch": "trace/baseline-column-transformer" if variant == "baseline_column_transformer" else None,
        "github_pr": "17" if variant == "baseline_column_transformer" else None,
        "base_paper": {
            "role": "primary_experiment_descriptor",
            **{k: v for k, v in base.items() if k not in ("trace_theory_sections", "base_papers")},
        },
        "trace_theory_paper": {
            **TRACE_THEORY_PAPER,
            "sections": base.get("trace_theory_sections", []),
        },
    }
    if base_papers:
        descriptor["base_papers"] = base_papers
        descriptor["base_paper"]["role"] = "model_experiment_descriptor"
    if descriptor.get("branch") is None:
        descriptor.pop("branch", None)
    if descriptor.get("github_pr") is None:
        descriptor.pop("github_pr", None)
    descriptor.update(
        {
            "agent_implementation": {
                "trace_language_csv": rel_trace,
                "trace_language_csv_absolute": str(vdir / "trace_language.csv"),
                "resource_envelope_rows": "2-21",
                "governance_bootstrap_rows": "22-26",
                "chomsky_audit": "sec/4 evaluation audit protocol (Type-3 consumer bounds)",
                "orchestrator": "paperbench.trace_pipeline.orchestrator.TracePipelineOrchestrator",
            },
            "experiment": {
                "hypothesis": hypothesis,
                "statistical_framework": "statistical_framework.md",
                "ablation_plan": "ablation_plan.json",
                "subdivision_manifest": "subdivision_manifest.json",
                "primary_metric": "rmse_post_ps",
                "smre": "mean_rmse_plus_std_across_folds",
            },
        }
    )
    if ablation_factors is not None:
        descriptor["experiment"]["ablation_factors"] = ablation_factors

    pf = paper_file_for_descriptor(variant, vdir)
    if pf:
        descriptor["paper_file"] = pf

    return descriptor


def write_experiment_descriptor(
    variant: str,
    *,
    out_dir: Path | None = None,
    rogii_root: Path | None = None,
    ablation_factors: list[dict] | None = None,
) -> Path:
    out_dir = out_dir or variant_dir(variant, rogii_root=rogii_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    desc = build_experiment_descriptor(
        variant, rogii_root=rogii_root, ablation_factors=ablation_factors
    )
    out = out_dir / "experiment_descriptor.json"
    out.write_text(json.dumps(desc, indent=2), encoding="utf-8")
    return out


def load_experiment_descriptor(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def render_paper_refs_md(descriptor: dict[str, Any]) -> str:
    """Human-readable paper + trace join for a variant directory."""
    variant = descriptor["variant"]
    base = descriptor["base_paper"]
    base_papers = descriptor.get("base_papers", [base])
    trace = descriptor["trace_theory_paper"]
    agent = descriptor["agent_implementation"]
    exp = descriptor["experiment"]

    lines = [
        f"# Experiment descriptor: {variant}",
        "",
        f"**Approach:** {descriptor['approach']}",
    ]
    if descriptor.get("branch"):
        lines.append(f"**Branch:** `{descriptor['branch']}`")
    if descriptor.get("github_pr"):
        lines.append(f"**PR:** #{descriptor['github_pr']}")
    lines.extend(["", "## Base papers (ablation / experiment design)", ""])

    for i, paper in enumerate(base_papers, start=1):
        role = paper.get("role", "experiment_descriptor")
        lines.extend(
            [
                f"### {i}. {paper['title']}",
                "",
                f"- **Role:** {role}",
                f"- **Authors:** {paper.get('short_authors', paper['authors'])}",
                f"- **Year / venue:** {paper.get('year', '?')} / {paper.get('venue', '?')}",
            ]
        )
        if paper.get("doi"):
            lines.append(f"- **DOI:** {paper['doi']}")
        if paper.get("url"):
            lines.append(f"- **URL:** {paper['url']}")
        lines.extend(["", "**Claims driving ablations:**"])
        for claim in paper.get("claims", []):
            lines.append(f"- {claim}")
        if paper.get("ablation_sections"):
            lines.append("")
            lines.append(f"**Ablation-relevant sections:** {', '.join(paper['ablation_sections'])}")
        if paper.get("trace_tokens"):
            lines.append("")
            lines.append(f"**Trace tokens:** `{', '.join(paper['trace_tokens'])}`")
        lines.append("")

    if not descriptor.get("base_papers") and base.get("supporting"):
        lines.extend(["**Supporting references:**"])
        for s in base["supporting"]:
            lines.append(f"- {s['authors']} ({s['year']}). *{s['title']}* — {s.get('role', '')}")
        lines.append("")

    lines.extend(
        [
            "## Trace theory paper (agent audit layer)",
            "",
            f"- **PaperBench id:** `{trace['paperbench_id']}`",
            f"- **Title:** {trace['title']}",
            f"- **Sections:** {', '.join(trace.get('sections', []))}",
            f"- **Role:** {trace['role']}",
            "",
            "## Agent implementation (`trace_language.csv`)",
            "",
            f"- **Path:** `{agent['trace_language_csv']}`",
            f"- **Resource envelopes:** rows {agent['resource_envelope_rows']}",
            f"- **Orchestrator:** `{agent['orchestrator']}`",
            "",
            "## Experiment linkage",
            "",
            f"- **Hypothesis:** {exp['hypothesis']}",
            f"- **Primary metric:** {exp['primary_metric']}",
            f"- **Ablation plan:** `{exp['ablation_plan']}`",
            f"- **Subdivision:** `{exp['subdivision_manifest']}`",
            f"- **Machine-readable descriptor:** `experiment_descriptor.json`",
            "",
        ]
    )
    return "\n".join(lines)


def write_paper_refs_md(descriptor: dict[str, Any], *, out_dir: Path) -> Path:
    out = out_dir / "paper_refs.md"
    out.write_text(render_paper_refs_md(descriptor), encoding="utf-8")
    return out
