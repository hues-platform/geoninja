"""Hydraulic gradient raster staging step.

This pipeline step stages a hydraulic gradient raster (currently Germany) into
the GeoNinja backend data directory.

The step is intentionally conservative: it does not resample or reproject the
data. Instead, it copies the source GeoTIFF (and optional GDAL aux XML) into
``backend/data`` and emits a JSON manifest containing provenance and basic raster
metadata read via Rasterio.

Entry point
-----------
The pipeline orchestrator calls :func:`run`:

        run(repo_root: Path, force: bool = False) -> None

Inputs
------
- Config file: ``data_pipeline/sources/hydr_grad/source.yaml``.
- Source files declared under ``files``.

Required config keys
--------------------
At minimum:

.. code-block:: yaml

        files:
            geotiff: path/to/hydr_grad_ger.tif
            gdal_aux_xml: path/to/hydr_grad_ger.tif.aux.xml  # optional

Optional keys (used in the manifest)
------------------------------------
- ``dataset``: dataset identifier/name
- ``quantity``: quantity name (defaults to ``hydraulic_gradient``)
- ``stored_unit``: unit semantics of stored values (defaults to ``percent``)
- ``scale_factor_to_dimensionless``: multiplier to convert stored values into a
    dimensionless gradient (defaults to ``0.01``)
- ``citation``, ``publisher``, ``url``, ``license_note`` and similar metadata

Outputs
-------
Written into ``backend/data``:

- ``hydr_grad_ger.tif`` (copy of input GeoTIFF)
- ``hydr_grad_ger.tif.aux.xml`` (optional copy, if provided)
- ``hydr_grad_ger.manifest.json`` (metadata/provenance)

Notes
-----
The script records basic raster metadata and a min/max range. For the current
raster size, reading band 1 to compute min/max is acceptable; if this step ever
becomes a bottleneck, the min/max computation can be made optional.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import date

import yaml

from geoninja_backend import __version__


def _resolve_repo_path(repo_root: Path, p: str) -> Path:
    """Resolve a path string from ``source.yaml`` into an absolute :class:`Path`.

    Args:
        repo_root: Repository root directory.
        p: Path string from YAML. Can be absolute, repository-relative, and may
            include ``~``.

    Returns:
        An absolute, normalized path.
    """
    path = Path(p).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def run(repo_root: Path, force: bool = False) -> None:
    """Stage the hydraulic gradient raster into the backend data directory.

    Args:
        repo_root: Repository root directory (used to locate config, inputs, and
            outputs).
        force: If ``True``, overwrite outputs even if they already exist.

    Reads:
        - ``data_pipeline/sources/hydr_grad/source.yaml``
        - The GeoTIFF specified at ``files.geotiff``.
        - Optionally the aux XML file at ``files.gdal_aux_xml``.

    Writes:
        - ``backend/data/hydr_grad_ger.tif``
        - ``backend/data/hydr_grad_ger.tif.aux.xml`` (if provided)
        - ``backend/data/hydr_grad_ger.manifest.json``

    Manifest contents:
        The manifest includes provenance (input file paths), plus basic raster
        metadata extracted via Rasterio (CRS, bounds, dimensions, dtype, nodata,
        and a min/max value range for band 1).

    Raises:
        FileNotFoundError: If the config file or any declared source file is
            missing.
        KeyError: If required config keys are missing (e.g., ``files.geotiff``).
        RuntimeError: If Rasterio is not installed.
    """
    src_yml = repo_root / "data_pipeline" / "sources" / "hydr_grad" / "source.yaml"
    backend_data_dir = repo_root / "backend" / "data"

    dst_tif = backend_data_dir / "hydr_grad_ger.tif"
    dst_aux = backend_data_dir / "hydr_grad_ger.tif.aux.xml"
    dst_mani = backend_data_dir / "hydr_grad_ger.manifest.json"

    if dst_tif.exists() and dst_mani.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    if not src_yml.exists():
        raise FileNotFoundError(f"Missing source config: {src_yml}")

    cfg = yaml.safe_load(src_yml.read_text(encoding="utf-8")) or {}

    files = cfg.get("files")
    if not isinstance(files, dict) or "geotiff" not in files:
        raise KeyError(
            "source.yaml must contain:\n"
            "files:\n"
            "  geotiff: <path-to-geotiff>\n"
            "  gdal_aux_xml: <optional path-to-.tif.aux.xml>\n"
        )

    # Resolve and validate source files
    input_paths: dict[str, Path] = {}
    missing: dict[str, Path] = {}
    for key, rel_path in files.items():
        p = _resolve_repo_path(repo_root, rel_path)
        input_paths[key] = p
        if not p.exists():
            missing[key] = p
    if missing:
        raise FileNotFoundError(
            "Missing hydraulic gradient source files:\n" + "\n".join(str(p) for p in missing.values())
        )

    backend_data_dir.mkdir(parents=True, exist_ok=True)

    # Read raster metadata via rasterio (lazy import)
    try:
        import rasterio
    except Exception as e:
        raise RuntimeError(
            "rasterio is required to process raster sources. Please install it in your environment."
        ) from e

    tif_path = input_paths["geotiff"]
    print(f"[info] Reading raster metadata:\n  {tif_path}")

    with rasterio.open(tif_path) as ds:
        # Basic raster properties
        width = ds.width
        height = ds.height
        count = ds.count
        dtype = ds.dtypes[0] if ds.dtypes else None
        nodata = ds.nodata
        crs = ds.crs.to_string() if ds.crs else None
        transform = ds.transform
        pixel_size_x = float(transform.a)
        pixel_size_y = float(transform.e)  # negative for north-up rasters
        bounds = ds.bounds

        # Min/max (cheap-ish; uses overviews if present, otherwise reads full band)
        # Optional: skip if too slow. For your size (2284x3101) it's acceptable.
        band1 = ds.read(1, masked=True)
        # Convert to python scalars for JSON
        data_min = float(band1.min()) if band1.count() > 0 else None
        data_max = float(band1.max()) if band1.count() > 0 else None
        valid_fraction = float(band1.count() / (width * height)) if width and height else None

    # Copy sources to backend/data (keep as raster)
    print(f"[info] Copying GeoTIFF -> {dst_tif}")
    shutil.copyfile(tif_path, dst_tif)

    aux_src = input_paths.get("gdal_aux_xml")
    aux_written = False
    if aux_src and aux_src.exists():
        print(f"[info] Copying AUX XML -> {dst_aux}")
        shutil.copyfile(aux_src, dst_aux)
        aux_written = True
    else:
        # Not fatal: GDAL can regenerate aux.xml
        print("[warn] No .tif.aux.xml provided; proceeding without it.")

    # Pull unit semantics from cfg (your current working assumption)
    stored_unit = cfg.get("stored_unit", "percent")
    scale_factor_to_dimensionless = cfg.get("scale_factor_to_dimensionless", 0.01)

    # Manifest
    manifest = {
        "dataset": {
            "name": cfg.get("dataset", "HYDR_GRAD_GER"),
            "version": __version__,
            "description": "Hydraulic gradient raster prepared for GeoNinja lookup",
            "format": "geotiff",
            "data_type": "raster",
            "bands": count,
            "dtype": dtype,
            "crs": crs or cfg.get("crs", ""),
            "width": width,
            "height": height,
            "pixel_size": {
                "x": pixel_size_x,
                "y": pixel_size_y,
                "unit": "m",
            },
            "bounds": {
                "left": bounds.left,
                "bottom": bounds.bottom,
                "right": bounds.right,
                "top": bounds.top,
                "crs": crs or cfg.get("crs", ""),
            },
            "nodata": nodata if nodata is not None else cfg.get("nodata", None),
            "value_range": {"min": data_min, "max": data_max},
            "valid_fraction": valid_fraction,
            "quantity": cfg.get("quantity", "hydraulic_gradient"),
            "stored_unit": stored_unit,
            "scale_factor_to_dimensionless": scale_factor_to_dimensionless,
            "notes": "Values assumed to be percent slope (%). Convert to dimensionless by * 0.01 before Darcy law.",
        },
        "source": {
            "origin": cfg.get("full_name", ""),
            "citation": cfg.get("citation", ""),
            "publisher": cfg.get("publisher", ""),
            "url": cfg.get("url", ""),
            "license_note": cfg.get("license_note", ""),
            "input_files": [p.as_posix() for p in input_paths.values()],
        },
        "processing": {
            "pipeline_step": "dp_hydraulic_gradient",
            "action": "copy",
            "from": [tif_path.as_posix()] + ([aux_src.as_posix()] if aux_src else []),
            "to": [dst_tif.as_posix()] + ([dst_aux.as_posix()] if aux_written else []),
            "modifications": (
                "no reprojection; keep EPSG:3857; "
                "assume stored values are percent; provide scale_factor_to_dimensionless=0.01"
            ),
        },
        "intended_use": {
            "application": "GeoNinja backend",
            "usage": "Raster sample-at-point lookup for hydraulic gradient; convert to dimensionless; compute v = K * i",
        },
        "generated": {
            "by": "geoninja data pipeline",
            "date": date.today().isoformat(),
        },
    }

    dst_mani.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote GeoTIFF:\n  -> {dst_tif}")
    print(f"[ok] Wrote manifest:\n  -> {dst_mani}")
