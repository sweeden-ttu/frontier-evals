#!/usr/bin/env python3
"""Symlink agent-tracing paper PDFs into PaperBench bundled data/rogii/papers."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

FRONTIER_ROOT = Path("/lustre/work/sweeden/frontier-evals/project/paperbench")
DEFAULT_SRC = Path("/lustre/work/sweeden/agent-tracing-trace-baseline/examples/rogii/papers")
DEFAULT_DST = FRONTIER_ROOT / "data" / "rogii" / "papers"


def _link_or_copy(src: Path, dst: Path, *, copy: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
    if copy:
        import shutil

        shutil.copy2(src, dst)
    else:
        os.symlink(src.resolve(), dst)


def sync_papers(src: Path, dst: Path, *, copy: bool = False) -> int:
    if not src.is_dir():
        raise SystemExit(f"source missing: {src}")
    n = 0
    for pdf in sorted(src.rglob("*.pdf")):
        rel = pdf.relative_to(src)
        target = dst / rel
        if pdf.stat().st_size < 5000:
            continue
        _link_or_copy(pdf, target, copy=copy)
        n += 1
    for meta in ("manifest.json", "README.md"):
        msrc = src / meta
        if msrc.is_file():
            _link_or_copy(msrc, dst / meta, copy=copy)
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--dst", type=Path, default=DEFAULT_DST)
    parser.add_argument("--copy", action="store_true", help="Copy instead of symlink")
    args = parser.parse_args()
    n = sync_papers(args.src, args.dst, copy=args.copy)
    print(f"Synced {n} PDFs from {args.src} -> {args.dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
