from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

# from data_pipeline.scripts.dp_glim import run as run_glim
from geoninja_dp.dp_rock_properties import run as run_rock_props

# from data_pipeline.scripts.dp_glhymps import run as run_glhymps
# from data_pipeline.scripts.dp_hydr_grad import run as run_hydr_grad

Step = Callable[[Path, bool], None]

# Ordered list of step callables that together form the full pipeline.
DATA_PIPELINE = [run_rock_props]


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


def run() -> int:
    """Run all pipeline steps.

    Returns:
        Process exit code: ``0`` on success, ``1`` on failure.
    """

    args = _parse_args()

    try:
        for step in DATA_PIPELINE:
            print(f"\n=== Running {step.__module__}.{step.__name__} ===")
            step(args.force)
        print("\n[ok] Pipeline complete.")
        return 0
    except Exception as exc:
        print(f"\n[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    run()
