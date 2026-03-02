import os
import shutil
from datetime import date

import geopandas as gpd
import numpy as np
import requests
import yaml
from pyproj import CRS
from tqdm import tqdm

from geoninja_dp import nav

# Paths
src_yaml_file = nav.DATA_SOURCES_DIR / "glhymps" / "source.yaml"
work_dir = nav.get_dp_work_dir() / "glhymps"
cache_dir = work_dir / "_cache"
dataverse_zip_dl_file = cache_dir / "glhymps_dataverse_dl.zip"
interior_zip_file = cache_dir / "GLHYMPS.zip"
dv_manifest_file = cache_dir / "MANIFEST.TXT"
dv_readme_file = cache_dir / "Readme_GLHYMPS2_0.txt"
dv_shp_file = cache_dir / "GLHYMPS.shp"
dv_shx_file = cache_dir / "GLHYMPS.shx"
dv_dbf_file = cache_dir / "GLHYMPS.dbf"
dv_prj_file = cache_dir / "GLHYMPS.prj"
dv_qpj_file = cache_dir / "GLHYMPS.qpj"
proc_parquet_file = work_dir / "glhymps.parquet"
proc_mani_file = work_dir / "glhymps.manifest.yaml"
tar_mani_file = nav.BACKEND_DATA_DIR / "glhymps.manifest.yaml"
tar_parquet_file = nav.BACKEND_DATA_DIR / "glhymps.parquet"

# Settings
publish_crs = 4326

def run(force: bool) -> None:
    # Skip if output exists and not forced
    if tar_mani_file.exists() and tar_parquet_file.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    # Source yaml
    if not src_yaml_file.exists():
        raise FileNotFoundError(f"Missing source config: {src_yaml_file}")
    src_yaml = yaml.safe_load(src_yaml_file.read_text(encoding="utf-8")) or {}

    # Work directory paths
    work_dir.mkdir(parents=True, exist_ok=True)

    # Pipeline steps
    _download(src_yaml, force)
    _extract(force)
    _process(src_yaml)
    _stage()
    print("[ok] GLHYMPS pipeline complete.")


def _download(src_yaml: dict, force: bool) -> None:
    # Read dataverse info from source yaml
    dv = src_yaml.get("dataverse")
    if not isinstance(dv, dict):
        raise KeyError(
            "source.yaml must contain a 'dataverse' mapping:\n"
            "dataverse:\n"
            "  base_url: <https://...>\n"
            "  persistent_id: <doi:...>\n"
        )

    # Handle paths and folders in cache directory
    base_url = dv.get("base_url")
    persistent_id = dv.get("persistent_id")
    if not base_url or not persistent_id:
        raise KeyError(
            "dataverse mapping must contain 'base_url' and 'persistent_id'"
        )
    if force and cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dataverse_zip_dl_file
    if not force and zip_path.exists():
        print(f"[skip] Dataverse download already exists: {zip_path}")
        return

    # Download zip
    print(f"[info] Downloading Dataverse dataset (~5min) to {zip_path}:\n  {persistent_id}\n  from: {base_url}")
    endpoint = f"{base_url.rstrip('/')}/api/access/dataset/:persistentId/"
    params = {"persistentId": persistent_id}
    with requests.get(endpoint, params=params, stream=True, timeout=300) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            hint = ""
            if r.status_code in (401, 403):
                hint = (
                    "\n[hint] This dataset or some files may be restricted."
                )
            raise RuntimeError(
                f"Dataverse download failed ({r.status_code}) for {persistent_id} from {base_url}.{hint}"
            ) from e
        total_size = int(r.headers.get("Content-Length", 0))
        chunk_size = 1024 * 1024
        with open(zip_path, "wb") as f, tqdm(
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
    print("[ok] Downloaded dataset ZIP")

def _extract(force: bool) -> None:
    # Extract zip
    expected_files = [interior_zip_file, dv_manifest_file, dv_readme_file]
    if not force and all(fi.exists() for fi in expected_files):
        print("[skip] Dataverse ZIP already extracted with expected files:")
        for fi in expected_files:
            print(f"  {fi}")
    else:
        print(f"[info] Extracting Dataverse ZIP (~30s):\n  {dataverse_zip_dl_file}")
        shutil.unpack_archive(dataverse_zip_dl_file, cache_dir)
        missing_files = [str(p) for p in expected_files if not p.exists()]
        if missing_files:
            raise FileNotFoundError(
                f"Expected files not found in extracted Dataverse ZIP: {missing_files}"
            )
        os.remove(dataverse_zip_dl_file)

    # Unzip interior zip file
    expected_files = [dv_shp_file, dv_shx_file, dv_dbf_file, dv_prj_file, dv_qpj_file]
    if not force and all(fi.exists() for fi in expected_files):
        print("[skip] Interior ZIP already extracted with expected files:")
        for fi in expected_files:
            print(f"  {fi}")
    else:
        print(f"[info] Extracting interior shape files (~30s) from:\n  {dataverse_zip_dl_file}")
        shutil.unpack_archive(interior_zip_file, cache_dir)
        missing_files = [str(p) for p in expected_files if not p.exists()]
        if missing_files:
            raise FileNotFoundError(
                f"Expected files not found in extracted {interior_zip_file.name}: {missing_files}"
            )
        os.remove(interior_zip_file)

def _process(src_yaml: dict) -> None:
    # Read shapefile
    print(f"[info] Reading shapefile (~2min):\n  {dv_shp_file}")
    gdf = gpd.read_file(
        dv_shp_file,
        columns=["geometry", "Porosity_x", "logK_Ferr_"],
        engine="pyogrio"
    )
    if gdf.empty:
        raise RuntimeError(f"Read empty GeoDataFrame from {dv_shp_file}")

    # CRS normalization
    if gdf.crs is None:
        raise RuntimeError(f"Input shapefile has no CRS: {dv_shp_file}")
    crs = CRS.from_user_input(gdf.crs)
    do_reproject = crs.to_epsg() != publish_crs
    if do_reproject:
        print(f"[info] Reprojecting (~3min) from: {crs.to_string()} to EPSG {publish_crs} ...")
        gdf = gdf.to_crs(epsg=publish_crs)

    # Geometry validation and fixing
    invalid = 0
    print(f"[info] Validating geometries (~3min) in GeoDataFrame with {len(gdf)} features ...")
    try:
        invalid = (~gdf.geometry.is_valid).sum()
        if invalid:
            print(f"[info] Found {invalid} invalid geometries. Attempting to fix (~15min) ...")
            gdf["geometry"] = [
                geom.buffer(0) if geom and not geom.is_valid else geom
                for geom in tqdm(gdf.geometry, desc="Fixing geometries")
            ]
            after_invalid = (~gdf.geometry.is_valid).sum()
            print(f"[info] Invalid geometries after fix: {after_invalid}")
        else:
            print("[ok] All geometries are valid.")
    except Exception as e:
        print(f"[warning] Geometry validation failed with error: {e}. Proceeding without geometry fixes.")

    # Select columns to keep (cols_to_keep[old_name] = new_name)
    cols_to_keep: dict[str, str] = {
        "geometry": "geometry",
        "Porosity_x": "porosity_x100",
        "logK_Ferr_": "logk_ferr_x100",
    }
    missing = [c for c in cols_to_keep if c not in gdf.columns]
    if missing:
        raise KeyError(f"GLHYMPS missing expected columns: {missing}. Available: {list(gdf.columns)}")
    gdf = gdf[list(cols_to_keep.keys())].rename(columns=cols_to_keep)

    # Porosity decode. GLHYMPS stores as percentage value, convert to decimal:
    gdf["porosity"] = gdf["porosity_x100"].astype("float64") / 100

    # Hydraulic conductivity K decode. GLHYMPS stores log10(K) multiplied by 100 ("x100"),
    # so divide by 100 to recover log10(K). Values >= 0 are treated as invalid and masked.
    log10_k = gdf["logk_ferr_x100"].astype("float64") / 100.0
    k_vals_to_drop = log10_k >= 0
    log10_k = log10_k.where(~k_vals_to_drop)  # Mask invalid values
    gdf["hydraulic_conductivity_m_s"] = np.power(10.0, log10_k) * 1e7

    # Reduce gdf to relevant columns
    gdf = gdf[["geometry", "porosity", "hydraulic_conductivity_m_s"]]

    # Write GeoParquet
    print(f"[info] Writing processed GeoDataFrame to GeoParquet (~1min):\n  {proc_parquet_file}")
    gdf.to_parquet(proc_parquet_file, index=False)

    # Save manifest
    proc_input_files = [
        dv_shp_file,
        dv_shx_file,
        dv_dbf_file,
        dv_prj_file,
        dv_qpj_file,
    ]
    proc_manifest = {
        "dataset": {
            "name": "GLHYMPS",
            "version": 2.0,
            "description": "GLHYMPS global hydrogeology dataset prepared for GeoNinja lookup",
            "format": "geoparquet",
            "geometry": "polygon",
            "crs": f"EPSG:{publish_crs}",
        },
        "source": {
            "origin": src_yaml.get("full_name", ""),
            "citation": src_yaml.get("citation", ""),
            "publisher": src_yaml.get("publisher", ""),
            "url": src_yaml.get("url", ""),
            "license_note": src_yaml.get("license_note", ""),
        },
        "processing": {
            "pipeline_step": "dp_glhymps",
            "action": "convert",
            "from": [p.as_posix() for p in proc_input_files],
            "to": tar_parquet_file.as_posix(),
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
    proc_mani_file.write_text(yaml.dump(proc_manifest), encoding="utf-8")
    for p in proc_input_files:
        os.remove(p)

def _stage() -> None:
    # Move processed parquet and manifest
    print(f"[info] Staging processed data to backend data directory:\n  {tar_parquet_file}\n  {tar_mani_file}")
    shutil.copyfile(proc_parquet_file, tar_parquet_file)
    shutil.copyfile(proc_mani_file, tar_mani_file)
    os.remove(proc_parquet_file)
    os.remove(proc_mani_file)
