"""Console entry point: ``chomsky-banned scan|init|check``.

Exit codes:
    0  — no error-severity hits found.
    1  — at least one error-severity hit, or ``--exit-nonzero-on-hit``
         was passed and any hit was found.

The CLI is deliberately dependency-light: ``rich`` is loaded only when
available (extras group ``cli``); without it we fall back to plain
prints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from chomsky_vv.banned.matcher import BannedTokenMatcher, Hit
from chomsky_vv.banned.policy import BannedTokenPolicy, default_policy, load_policy


def _load_policy_from_arg(arg: str | None) -> BannedTokenPolicy:
    candidate = arg or os.environ.get("CHOMSKY_BANNED_POLICY")
    if candidate:
        return load_policy(candidate)
    return default_policy()


def _format_hits_plain(hits: list[Hit]) -> str:
    if not hits:
        return "no banned-token hits found."
    lines = []
    for h in hits:
        lines.append(
            f"{h.severity.upper():<5}  banned:{h.token:<12}  "
            f"{h.file}:{h.line}:{h.col}  [{h.kind}]  {h.excerpt[:80]}"
        )
    lines.append(f"\n{len(hits)} hit(s).")
    return "\n".join(lines)


def _format_hits_rich(hits: list[Hit]) -> None:  # pragma: no cover - optional
    try:
        from rich.console import Console  # type: ignore[import-not-found]
        from rich.table import Table  # type: ignore[import-not-found]
    except ImportError:
        print(_format_hits_plain(hits))
        return
    console = Console()
    if not hits:
        console.print("[green]no banned-token hits found.[/green]")
        return
    table = Table(title=f"chomsky-banned: {len(hits)} hit(s)")
    table.add_column("severity")
    table.add_column("token")
    table.add_column("file:line:col")
    table.add_column("kind")
    table.add_column("excerpt", overflow="fold")
    sev_color = {"error": "red", "warn": "yellow", "info": "cyan"}
    for h in hits:
        color = sev_color.get(h.severity, "white")
        table.add_row(
            f"[{color}]{h.severity}[/{color}]",
            f"banned:{h.token}",
            f"{h.file}:{h.line}:{h.col}",
            h.kind,
            h.excerpt[:120],
        )
    console.print(table)


def _hits_to_json(hits: list[Hit]) -> str:
    return json.dumps(
        {
            "n_hits": len(hits),
            "hits": [
                {
                    "token": h.token,
                    "file": h.file,
                    "line": h.line,
                    "col": h.col,
                    "kind": h.kind,
                    "severity": h.severity,
                    "excerpt": h.excerpt,
                }
                for h in hits
            ],
        },
        indent=2,
    )


def _scan_paths(paths: list[str], policy: BannedTokenPolicy) -> list[Hit]:
    matcher = BannedTokenMatcher(policy)
    hits: list[Hit] = []
    for p in paths:
        hits.extend(matcher.scan_path(Path(p)))
    return hits


def _exit_for(hits: list[Hit], force_nonzero: bool) -> int:
    if not hits:
        return 0
    if force_nonzero:
        return 1
    return 1 if any(h.severity == "error" for h in hits) else 0


def _cmd_scan(args: argparse.Namespace) -> int:
    policy = _load_policy_from_arg(args.policy)
    hits = _scan_paths(args.paths, policy)
    if args.json:
        print(_hits_to_json(hits))
    elif args.rich:
        _format_hits_rich(hits)
    else:
        print(_format_hits_plain(hits))
    return _exit_for(hits, args.exit_nonzero_on_hit)


def _cmd_check(args: argparse.Namespace) -> int:
    policy = _load_policy_from_arg(args.policy)
    hits = _scan_paths([args.path], policy)
    if args.json:
        print(_hits_to_json(hits))
    else:
        print(_format_hits_plain(hits))
    return _exit_for(hits, force_nonzero=True)


def _cmd_init(args: argparse.Namespace) -> int:
    src = Path(__file__).parent / "policy.yaml"
    out = Path(args.out)
    if out.exists() and not args.force:
        print(
            f"refusing to overwrite existing {out} (pass --force to clobber).",
            file=sys.stderr,
        )
        return 1
    out.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote default policy to {out}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chomsky-banned",
        description="Scan files/dirs/text for banned tokens (chomsky_vv).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Scan paths for banned-token hits.")
    p_scan.add_argument("paths", nargs="+", help="Files or directories to scan.")
    p_scan.add_argument("--policy", help="Path to a policy YAML (overrides default).")
    p_scan.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    p_scan.add_argument("--rich", action="store_true", help="Pretty-print using rich.")
    p_scan.add_argument(
        "--exit-nonzero-on-hit",
        action="store_true",
        help="Exit 1 on any hit, regardless of severity.",
    )
    p_scan.set_defaults(func=_cmd_scan)

    p_check = sub.add_parser(
        "check",
        help="Single-file/dir check, exit 1 on any hit. Suitable for CI.",
    )
    p_check.add_argument("path")
    p_check.add_argument("--policy")
    p_check.add_argument("--json", action="store_true")
    p_check.set_defaults(func=_cmd_check)

    p_init = sub.add_parser("init", help="Write the default policy YAML to disk.")
    p_init.add_argument("--out", default="banned-policy.yaml")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=_cmd_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
