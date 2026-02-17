"""Data pipeline entrypoint.

This module is a thin orchestrator that runs a fixed sequence of data-ingestion/
preprocessing steps found under :mod:`data_pipeline.scripts`.

Options:
    --force  Rebuild outputs even if destination files already exist.

Each pipeline step is a callable with the signature ``(repo_root: Path, force: bool)``.
The ``repo_root`` is inferred from this file's location so steps can resolve their
inputs/outputs using repository-relative paths.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from data_pipeline.scripts.dp_glim import run as run_glim
from data_pipeline.scripts.dp_rock_properties import run as run_rock_props
from data_pipeline.scripts.dp_glhymps import run as run_glhymps
from data_pipeline.scripts.dp_hydr_grad import run as run_hydr_grad

Step = Callable[[Path, bool], None]

# Ordered list of step callables that together form the full pipeline.
DATA_PIPELINE = [run_glim, run_rock_props, run_glhymps, run_hydr_grad]


def _repo_root_from_here() -> Path:
    """Return the repository root directory.

    Assumes this file lives at ``<repo_root>/data_pipeline/run.py``.
    """
    return Path(__file__).resolve().parents[1]


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    p = argparse.ArgumentParser(
        prog="data_pipeline.run",
        description="Run the repository data pipeline steps in order.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Rebuild outputs even if destination files already exist.",
    )
    return p.parse_args()


def main() -> int:
    """Run all pipeline steps.

    Returns:
        Process exit code: ``0`` on success, ``1`` on failure.
    """

    args = _parse_args()
    repo_root = _repo_root_from_here()

    try:
        for step in DATA_PIPELINE:
            print(f"\n=== Running {step.__module__}.{step.__name__} ===")
            step(repo_root, args.force)
        print("\n[ok] Pipeline complete.")
        return 0
    except Exception as exc:
        print(f"\n[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
