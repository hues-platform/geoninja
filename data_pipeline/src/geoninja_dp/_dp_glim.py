"""GLiM ingestion step (copy + manifest).

This pipeline step stages the GLiM (Global Lithological Map) dataset for the
GeoNinja backend.

Unlike other steps that read source formats and perform transformations, GLiM is
assumed to already be provided as a Parquet dataset suitable for point-in-polygon
lookups. This script therefore:

- reads ``data_pipeline/sources/glim/source.yaml`` to locate the source Parquet
    file;
- copies the Parquet file into ``backend/data`` as ``glim.parquet``;
- writes a corresponding provenance/metadata manifest
    (``backend/data/glim.manifest.json``).

Entry point
-----------
The pipeline orchestrator calls :func:`run`:

        run(repo_root: Path, force: bool = False) -> None

Config schema
-------------
The config must provide the Parquet path under ``files.parquet``:

.. code-block:: yaml

        files:
            parquet: path/to/glim.parquet

Paths may be absolute or repository-relative.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import date

import yaml

from geoninja_backend import __version__


def run(repo_root: Path, force: bool = False) -> None:
    """Stage the GLiM dataset into the backend data directory.

    Args:
        repo_root: Repository root directory (used to locate config, inputs, and
            the backend data directory).
        force: If ``True``, overwrite outputs even if they already exist.

    Reads:
        - ``data_pipeline/sources/glim/source.yaml`` for the input file path and
          optional metadata (e.g., ``citation``, ``publisher``, ``url``).
        - The Parquet file referenced at ``files.parquet``.

    Writes:
        - ``backend/data/glim.parquet`` (a byte-for-byte copy of the source)
        - ``backend/data/glim.manifest.json`` (metadata/provenance)

    Behavior:
        - If both output files already exist and ``force`` is ``False``, the step
          prints a skip message and returns.

    Raises:
        FileNotFoundError: If the config file or the declared Parquet file is
            missing.
        KeyError: If ``source.yaml`` does not contain ``files.parquet``.
    """
    src_yml = repo_root / "data_pipeline" / "sources" / "glim" / "source.yaml"
    backend_data_dir = repo_root / "backend" / "data"
    dst = backend_data_dir / "glim.parquet"
    dst_mani = backend_data_dir / "glim.manifest.json"

    if dst.exists() and dst_mani.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    if not src_yml.exists():
        raise FileNotFoundError(f"Missing source config: {src_yml}")

    cfg = yaml.safe_load(src_yml.read_text(encoding="utf-8")) or {}
    try:
        src_path_str_glim = cfg["files"]["parquet"]
    except Exception as e:
        raise KeyError(
            "source.yaml must contain:\n"
            "files:\n"
            "  parquet: <path-to-parquet>\n"
        ) from e

    src = Path(src_path_str_glim).expanduser()
    if not src.is_absolute():
        src = (repo_root / src).resolve()
    else:
        src = src.resolve()

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    backend_data_dir.mkdir(parents=True, exist_ok=True)

    if dst.exists():
        print(f"[info] Destination exists, overwriting: {dst}")
    else:
        print(f"[info] Writing new dataset: {dst}")

    shutil.copyfile(src, dst)
    print(f"[ok] Copied GLiM parquet:\n  {src}\n  -> {dst}")

    manifest = {
        "dataset": {
            "name": "GLiM",
            "version": __version__,
            "description": "GLiM global lithology dataset prepared for GeoNinja lookup",
            "format": "parquet",
            "geometry": "polygon",
        },
        "source": {
            "origin": cfg.get("full_name", ""),
            "citation": cfg.get("citation", ""),
            "publisher": cfg.get("publisher", ""),
            "url": cfg.get("url", ""),
            "license_note": cfg.get("license_note", ""),
            "input_file": src.as_posix(),
        },
        "processing": {
            "pipeline_step": "dp_glim",
            "action": "copy",
            "from": src.as_posix(),
            "to": dst.as_posix(),
            "modifications": "none",
        },
        "intended_use": {
            "application": "GeoNinja backend",
            "usage": "Point-in-polygon lithology lookup",
        },
        "generated": {
            "by": "geoninja data pipeline",
            "date": date.today().isoformat(),
        },
    }

    dst_mani.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] Wrote manifest:\n  -> {dst_mani}")
