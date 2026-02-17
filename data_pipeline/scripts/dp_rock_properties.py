"""Rock properties staging step (CSV + manifest).

This pipeline step stages a small reference table of representative bulk rock
properties keyed by GLiM lithology codes.

The backend uses this lookup table to derive or parameterize analysis inputs
based on lithology (e.g., density, heat capacity, thermal conductivity).

This step performs no transformation of the tabular data: it copies the source
CSV into ``backend/data`` and writes a manifest JSON that documents the schema
and provenance.

Entry point
-----------
The pipeline orchestrator calls :func:`run`:

    run(repo_root: Path, force: bool = False) -> None

Config schema
-------------
The config file ``data_pipeline/sources/rock_properties/source.yaml`` must
contain:

.. code-block:: yaml

    files:
      csv: path/to/rock_properties.csv

The CSV path may be absolute or repository-relative.

Outputs
-------
Written into ``backend/data``:

- ``rock_properties.csv``
- ``rock_properties.manifest.json``
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import yaml

from geoninja_backend import __version__


def run(repo_root: Path, force: bool = False) -> None:
    """Stage the rock properties CSV into the backend data directory.

    Args:
        repo_root: Repository root directory (used to locate config, inputs, and
            outputs).
        force: If ``True``, overwrite outputs even if they already exist.

    Reads:
        - ``data_pipeline/sources/rock_properties/source.yaml``
        - The CSV file referenced at ``files.csv``.

    Writes:
        - ``backend/data/rock_properties.csv`` (byte-for-byte copy of the source)
        - ``backend/data/rock_properties.manifest.json`` (schema + provenance)

    Behavior:
        If both output files already exist and ``force`` is ``False``, prints a
        skip message and returns.

    Raises:
        FileNotFoundError: If the config file or the declared CSV file is missing.
        KeyError: If ``source.yaml`` does not contain ``files.csv``.
    """
    src_yml = repo_root / "data_pipeline" / "sources" / "rock_properties" / "source.yaml"
    backend_data_dir = repo_root / "backend" / "data"
    dst = backend_data_dir / "rock_properties.csv"
    dst_mani = backend_data_dir / "rock_properties.manifest.json"

    if dst.exists() and dst_mani.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    if not src_yml.exists():
        raise FileNotFoundError(f"Missing source config: {src_yml}")

    cfg = yaml.safe_load(src_yml.read_text(encoding="utf-8")) or {}
    try:
        src_path_str = cfg["files"]["csv"]
    except Exception as e:
        raise KeyError(
            "source.yaml must contain:\n"
            "files:\n"
            "  csv: <path-to-csv>\n"
        ) from e

    src = Path(src_path_str).expanduser()
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
    print(f"[ok] Copied rock properties CSV:\n  {src}\n  -> {dst}")

    # Align manifest structure with glim.manifest.json; leave source fields blank for now.
    manifest = {
        "dataset": {
            "name": "Rock properties by lithology",
            "version": __version__,
            "description": "Representative bulk thermophysical rock properties mapped to GLiM lithology keys for GeoNinja parameter derivation",
            "format": "csv",
            "schema": {
                "primary_key": "litho_key",
                "fields": [
                    {"name": "litho_key", "type": "string", "description": "GLiM lithology key (e.g., 'su', 'ss', 'mt')"},
                    {"name": "density_kg_m3", "type": "number", "unit": "kg/m^3", "description": "Rock density"},
                    {"name": "spec_heat_cap_j_kgK", "type": "number", "unit": "J/(kg*K)", "description": "Specific heat capacity"},
                    {"name": "therm_cond_w_mK", "type": "number", "unit": "W/(m*K)", "description": "Thermal conductivity"},
                ],
            },
        },
        "source": {
            "origin": "",
            "citation": "",
            "input_file": src.as_posix(),
        },
        "processing": {
            "pipeline_step": "dp_rock_properties",
            "action": "copy",
            "from": src.as_posix(),
            "to": dst.as_posix(),
            "modifications": "none",
        },
        "intended_use": {
            "application": "GeoNinja backend",
            "usage": [
                "Derivation of rockDensity parameter",
                "Derivation of rockSpecHeatCap parameter",
                "Derivation of rockThermCond parameter",
            ],
        },
        "generated": {
            "by": "geoninja data pipeline",
            "date": date.today().isoformat(),
        },
    }

    dst_mani.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote manifest:\n  -> {dst_mani}")
