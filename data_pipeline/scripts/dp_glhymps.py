"""GLHYMPS ingestion + normalization step.

This module implements the data-pipeline step that converts the GLHYMPS vector
dataset (distributed as an ESRI Shapefile) into a GeoParquet file used by the
GeoNinja backend.

Entry point
-----------
The pipeline orchestrator calls :func:`run` with a repository root directory:

        run(repo_root: Path, force: bool = False) -> None

Inputs
------
- Config file: ``data_pipeline/sources/glhymps/source.yaml``.
- Source files: fetched from a Dataverse dataset (ZIP bundle), then read as an
  ESRI Shapefile.

The config must contain:

.. code-block:: yaml

        dataverse:
            base_url: "https://borealisdata.ca"
            persistent_id: "doi:10.5683/SP2/TTJNIU"
            cache_dir: "data_pipeline/sources/glhymps/_cache"
            api_token_env: "DATAVERSE_API_TOKEN"  # optional; required for restricted files

        files:
            shp: data_pipeline/sources/glhymps/_cache/GLHYMPS.shp
            shx: data_pipeline/sources/glhymps/_cache/GLHYMPS.shx
            dbf: data_pipeline/sources/glhymps/_cache/GLHYMPS.dbf
            prj: data_pipeline/sources/glhymps/_cache/GLHYMPS.prj
            qpj: data_pipeline/sources/glhymps/_cache/GLHYMPS.qpj

Paths can be absolute or repository-relative.

Outputs
-------
Written into ``backend/data``:

- ``glhymps.parquet``: GeoParquet with geometry and selected numeric attributes.
- ``glhymps.manifest.json``: metadata and provenance for the generated dataset.

Processing summary
------------------
- Read shapefile via GeoPandas.
- Ensure the input has a CRS; reproject to EPSG:4326 if necessary.
- Attempt to repair invalid geometries (best-effort) using the ``buffer(0)``
    fallback.
- Select and rename expected columns, then compute:
    - ``porosity`` from ``Porosity_x`` (stored as percent * 100)
    - ``hydraulic_conductivity_m_s`` from ``logK_Ferr_`` (stored as log10(K) * 100)

Notes
-----
This step assumes the GLHYMPS attribute names match the expected shapefile
schema (notably ``Porosity_x`` and ``logK_Ferr_``). If upstream data changes,
this script will raise a ``KeyError`` and list the available columns.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import requests
import yaml
from pyproj import CRS
from tqdm import tqdm

from geoninja_backend import __version__


def run(repo_root: Path, force: bool = False) -> None:
    """Build the GLHYMPS GeoParquet dataset and manifest.

    Args:
        repo_root: Repository root directory (used to resolve config, inputs, and
            output locations).
        force: If ``True``, rebuild outputs even when destination files already
            exist (and re-download sources).

    Reads:
        - ``data_pipeline/sources/glhymps/source.yaml`` for Dataverse config and
          extracted shapefile paths under ``files``.
        - Dataverse dataset ZIP bundle (downloaded into cache dir), then shapefile
          components declared under ``files``.

    Writes:
        - ``backend/data/glhymps.parquet``
        - ``backend/data/glhymps.manifest.json``

    Raises:
        FileNotFoundError: If the config or any declared input file is missing.
        KeyError: If required config keys or required source columns are missing.
        RuntimeError: If the dataset is empty, missing a CRS, or GeoPandas is not
            available, or if Dataverse download fails.
    """
    src_yml = repo_root / "data_pipeline" / "sources" / "glhymps" / "source.yaml"
    backend_data_dir = repo_root / "backend" / "data"
    dst_parquet = backend_data_dir / "glhymps.parquet"
    dst_mani = backend_data_dir / "glhymps.manifest.json"

    if dst_parquet.exists() and dst_mani.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    if not src_yml.exists():
        raise FileNotFoundError(f"Missing source config: {src_yml}")

    cfg: dict[str, Any] = yaml.safe_load(src_yml.read_text(encoding="utf-8")) or {}

    # Dataverse is mandatory
    dv = cfg.get("dataverse")
    if not isinstance(dv, dict):
        raise KeyError(
            "source.yaml must contain a 'dataverse' mapping:\n"
            "dataverse:\n"
            "  base_url: <https://...>\n"
            "  persistent_id: <doi:...>\n"
            "  cache_dir: <repo-relative-cache-dir>\n"
            "  api_token_env: <ENV_VAR_NAME>  # optional\n"
        )

    # Validate files mapping (unchanged expectations)
    files = cfg.get("files")
    if (not isinstance(files, dict)
            or not all(key in files for key in ("shp", "shx", "dbf", "prj", "qpj"))):
        raise KeyError(
            "source.yaml must contain:\n"
            "files:\n"
            "  shp: <path-to-shapefile>\n"
            "  shx: <path-to-shapefile-index>\n"
            "  dbf: <path-to-dbase-file>\n"
            "  prj: <path-to-prj-file>\n"
            "  qpj: <path-to-qpj-file>\n"
        )

    # Dataverse download + extract into cache (mandatory)
    _ensure_dataverse_cache(repo_root=repo_root, dv=dv, force=force)

    # Validate that all declared source files exist (helps provenance/debugging)
    input_paths: dict[str, Path] = {}
    missing: dict[str, Path] = {}
    for key, rel_path in files.items():
        p = _resolve_repo_path(repo_root, rel_path)
        input_paths[key] = p
        if not p.exists():
            missing[key] = p
    if missing:
        raise FileNotFoundError(
            "Missing GLHYMPS source files after Dataverse extraction:\n"
            + "\n".join(str(p) for p in missing.values())
        )

    backend_data_dir.mkdir(parents=True, exist_ok=True)

    # Lazy geopandas import
    try:
        import geopandas as gpd
    except Exception as e:
        raise RuntimeError(
            "geopandas is required to process GLHYMPS. Please install it in your environment."
        ) from e

    # Read shapefile
    print(f"[info] Reading shapefile:\n  {input_paths['shp']}")
    gdf = gpd.read_file(input_paths["shp"])

    if gdf.empty:
        raise RuntimeError("GLHYMPS shapefile contains no data.")

    # CRS normalization
    if gdf.crs is None:
        raise RuntimeError(
            "GLHYMPS input has no CRS. Ensure the .prj is present and readable."
        )

    # CRS normalization
    crs = CRS.from_user_input(gdf.crs)
    do_reproject = crs.to_epsg() != 4326
    if do_reproject:
        print(f"[info] Reprojecting from {crs.to_string()} -> EPSG:4326")
        gdf = gdf.to_crs(epsg=4326)

    # Geometry validation/fixing
    invalid = 0
    try:
        invalid = (~gdf.geometry.is_valid).sum()
        if invalid:
            print(f"[info] Fixing {invalid} invalid geometries (buffer(0) fallback)")
            gdf["geometry"] = [
                geom.buffer(0) if geom and not geom.is_valid else geom
                for geom in tqdm(gdf.geometry, desc="Fixing geometries")
            ]
            after_invalid = (~gdf.geometry.is_valid).sum()
            print(f"[info] Invalid geometries after fix: {after_invalid}")
    except Exception as e:
        print(f"[warn] Geometry validity check/fix failed: {e}")

    # Select columns to keep (cols_to_keep[old_name] = new_name)
    cols_to_keep: dict[str, str] = {
        "geometry": "geometry",
        "Porosity_x": "porosity_x100",
        "logK_Ferr_": "logk_ferr_x100",
    }
    missing = [c for c in cols_to_keep if c not in gdf.columns]
    if missing:
        print(f"[error] GLHYMPS missing expected columns: {missing}. Available: {list(gdf.columns)}")
        raise KeyError(f"GLHYMPS missing expected columns: {missing}. Available: {list(gdf.columns)}")
    gdf = gdf[list(cols_to_keep.keys())].rename(columns=cols_to_keep)

    # Porosity decode
    #
    # GLHYMPS stores porosity as (percent * 100). Example:
    #   Porosity_x = 1234  ->  12.34%
    # so we divide by 100 to get percent and by 100 again to get fraction.
    gdf["porosity"] = gdf["porosity_x100"].astype("float64") / 100.0

    # Hydraulic conductivity K
    #
    # GLHYMPS stores log10(K) multiplied by 100 ("x100"), so divide by 100 to
    # recover log10(K). Values >= 0 are treated as invalid and masked.
    #
    # Note: The final scaling by 1e7 is retained as-is to preserve the existing
    # behavior of the pipeline.
    log10_k = gdf["logk_ferr_x100"].astype("float64") / 100.0
    k_vals_to_drop = log10_k >= 0
    log10_k = log10_k.where(~k_vals_to_drop)  # Mask invalid values
    gdf["hydraulic_conductivity_m_s"] = np.power(10.0, log10_k) * 1e7

    # Reduce gdf to relevant columns
    gdf = gdf[["geometry", "porosity", "hydraulic_conductivity_m_s"]]

    # Write GeoParquet
    if dst_parquet.exists():
        print(f"[info] Destination exists, overwriting: {dst_parquet}")
    else:
        print(f"[info] Writing new dataset: {dst_parquet}")
    gdf.to_parquet(dst_parquet, index=False)
    print(f"[ok] Wrote GeoParquet:\n  -> {dst_parquet}")

    # Manifest
    manifest = {
        "dataset": {
            "name": "GLHYMPS",
            "version": __version__,
            "description": "GLHYMPS global hydrogeology dataset prepared for GeoNinja lookup",
            "format": "geoparquet",
            "geometry": "polygon",
            "crs": "EPSG:4326",
        },
        "source": {
            "origin": cfg.get("full_name", ""),
            "citation": cfg.get("citation", ""),
            "publisher": cfg.get("publisher", ""),
            "url": cfg.get("url", ""),
            "license_note": cfg.get("license_note", ""),
            "input_files": [p.as_posix() for p in input_paths.values()]
        },
        "processing": {
            "pipeline_step": "dp_glhymps",
            "action": "convert",
            "from": [p.as_posix() for p in input_paths.values()],
            "to": dst_parquet.as_posix(),
            "modifications":
                f"{'reproject_to_epsg_4326; ' if do_reproject else ''}"
                f"{'fix invalid geometries (buffer0, best effort)' if invalid else ''}"
                f"set {k_vals_to_drop.sum()} hydraulic conductivity vals to NaN where permeability >= 1 m/s",
        },
        "intended_use": {
            "application": "GeoNinja backend",
            "usage": "Point-in-polygon lookup for hydraulic conductivity",
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


def _ensure_dataverse_cache(*, repo_root: Path, dv: dict[str, Any], force: bool) -> None:
    """Download+extract Dataverse dataset ZIP into cache_dir.

    Behavior:
      - If force=True: delete cache_dir and re-download.
      - If force=False: download only if cache_dir looks empty (no files) OR the
        ZIP is not present. Downstream file existence checks are the source of truth.
    """
    base_url = dv.get("base_url")
    persistent_id = dv.get("persistent_id")
    cache_dir_rel = dv.get("cache_dir")
    token_env = dv.get("api_token_env")  # optional; required for restricted datasets/files

    if not base_url or not persistent_id or not cache_dir_rel:
        raise KeyError(
            "dataverse must contain:\n"
            "  base_url: <https://...>\n"
            "  persistent_id: <doi:...>\n"
            "  cache_dir: <repo-relative-cache-dir>\n"
            "Optional:\n"
            "  api_token_env: <ENV_VAR_NAME>\n"
        )

    cache_dir = _resolve_repo_path(repo_root, str(cache_dir_rel))
    zip_path = cache_dir / "dataverse_dataset.zip"

    if force and cache_dir.exists():
        shutil.rmtree(cache_dir)

    cache_dir.mkdir(parents=True, exist_ok=True)

    looks_empty = not any(cache_dir.iterdir())
    if not force and zip_path.exists() and not looks_empty:
        # Cache already populated; do not re-download.
        return

    token = os.getenv(str(token_env)) if token_env else None

    print(f"[info] Downloading Dataverse dataset bundle:\n  {persistent_id}\n  from: {base_url}")
    _dataverse_download_dataset_zip(
        base_url=str(base_url),
        persistent_id=str(persistent_id),
        dst_zip=zip_path,
        token=token,
    )

    print(f"[info] Extracting ZIP into:\n  {cache_dir}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(cache_dir)
    print("[ok] Extract complete")


def _dataverse_download_dataset_zip(
    *,
    base_url: str,
    persistent_id: str,
    dst_zip: Path,
    token: str | None,
) -> None:
    """Download a Dataverse dataset bundle (zip) by persistentId to dst_zip.

    Endpoint (Dataverse Data Access API):
        GET {base_url}/api/access/dataset/:persistentId/?persistentId=<doi>

    Displays a tqdm progress bar during download.
    """
    endpoint = f"{base_url.rstrip('/')}/api/access/dataset/:persistentId/"
    params = {"persistentId": persistent_id}

    headers: dict[str, str] = {}
    if token:
        headers["X-Dataverse-key"] = token

    with requests.get(endpoint, params=params, headers=headers, stream=True, timeout=300) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            hint = ""
            if r.status_code in (401, 403):
                hint = (
                    "\n[hint] This dataset or some files may be restricted. "
                    "Set dataverse.api_token_env to an environment variable "
                    "containing a Dataverse API token with access."
                )
            raise RuntimeError(
                f"Dataverse download failed ({r.status_code}) for {persistent_id} from {base_url}.{hint}"
            ) from e

        total_size = int(r.headers.get("Content-Length", 0))
        chunk_size = 1024 * 1024  # 1 MB

        dst_zip.parent.mkdir(parents=True, exist_ok=True)

        with open(dst_zip, "wb") as f, tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading GLHYMPS",
        ) as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

    print(f"[ok] Downloaded dataset ZIP:\n  -> {dst_zip}")


def _resolve_repo_path(repo_root: Path, p: str) -> Path:
    """Resolve a path string from ``source.yaml`` into an absolute :class:`Path`.

    Args:
        repo_root: Repository root directory.
        p: Path string from YAML. Can be absolute, repository-relative, and may
            include a home-directory shortcut (``~``).

    Returns:
        An absolute, normalized path.
    """
    path = Path(p).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()
