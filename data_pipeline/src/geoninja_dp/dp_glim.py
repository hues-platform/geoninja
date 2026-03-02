import os
import shutil
from datetime import date

import numpy as np
import rasterio
import requests
import yaml
from rasterio.transform import from_origin

from geoninja_dp import nav

# Paths
src_yml_file = nav.DATA_SOURCES_DIR / "glim" / "source.yaml"
work_dir = nav.get_dp_work_dir() / "glim"
cache_dir = work_dir / "_cache"
pangea_zip_dl_file = cache_dir / "hartmann-moosdorf_2012.zip"
glim_asc_file = cache_dir / "glim_wgs84_0point5deg.txt.asc"
glim_txt_file = cache_dir / "Classnames.txt"
proc_tif_file = work_dir / "glim.tif"
proc_mani_file = work_dir / "glim.manifest.yaml"
tar_mani_file = nav.BACKEND_DATA_DIR / "glim.manifest.yaml"
tar_tif_file = nav.BACKEND_DATA_DIR / "glim.tif"
tar_txt_file = nav.BACKEND_DATA_DIR / "glim.txt"

# Settings
publish_crs = 4326

def run(force: bool) -> None:
    # Skip if output exists and not forced
    if tar_tif_file.exists() and tar_mani_file.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    # Source yaml
    if not src_yml_file.exists():
        raise FileNotFoundError(f"Missing source config: {src_yml_file}")
    src_yaml = yaml.safe_load(src_yml_file.read_text(encoding="utf-8")) or {}

    # Work directory
    work_dir.mkdir(parents=True, exist_ok=True)

    # Pipeline steps
    _download(src_yaml, force)
    _extract(force)
    _process(src_yaml)
    _stage()

def _download(src_yaml: dict, force: bool) -> None:
    # Read pangea info from source yaml
    pangea = src_yaml.get("pangea")
    if not isinstance(pangea, dict):
        raise KeyError(
            "source.yaml must contain:\n"
            "pangea:\n"
            "  url: <Pangea GLiM url>\n"
        )

    # Handle paths and folders in cache directory
    url = pangea.get("url")
    if not url:
        raise KeyError("pangea mapping must contain 'url'")

    if force and cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = pangea_zip_dl_file
    if not force and zip_path.exists():
        print(f"[skip] Pangea download already exists: {zip_path}")
        return

    # Download zip
    print(f"[info] Downloading GLiM to {zip_path} from {url}")
    with requests.get(url, stream=True, timeout=300) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code in (401, 403):
                hint = (
                    "\n[hint] This dataset or some files may be restricted."
                )
            raise RuntimeError(
                f"Pangea download failed ({r.status_code}) from {url}.{hint}"
            ) from e
        chunk_size = 1024 * 1024
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
    print(f"[ok] Downloaded GLiM to {zip_path}")


def _extract(force: bool) -> None:
    # Extract zip
    expected_file = [glim_asc_file, glim_txt_file]
    if not force and all(fi.exists() for fi in expected_file):
        print("[skip] Pangea zip already extracted with expected files:")
        for fi in expected_file:
            print(f"  {fi}")
        return
    else:
        print(f"[info] Extracting GLiM zip:\n {pangea_zip_dl_file}")
        shutil.unpack_archive(pangea_zip_dl_file, cache_dir)
        missing_files = [fi for fi in expected_file if not fi.exists()]
        if missing_files:
            raise FileNotFoundError(
                f"Expected files not found in Pangea ZIP: {missing_files}"
            )
        os.remove(pangea_zip_dl_file)


def _process(src_yaml: dict) -> None:
    # Read ASCII file
    print(f"[info] Reading GLiM ASCII grid:\n  {glim_asc_file}")
    with open(glim_asc_file) as f:
        header = {}
        for _ in range(6):
            key, value = f.readline().split()
            header[key.lower()] = float(value)
        data = np.loadtxt(f)

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    xll = header["xllcorner"]
    yll = header["yllcorner"]
    cellsize = header["cellsize"]
    nodata = header["nodata_value"]

    # ASCII grid is top-left origin btu header gives lower-left
    transform = from_origin(
        xll,
        yll + nrows * cellsize,
        cellsize,
        cellsize
    )

    print(f"[info] Writing processed GLiM GeoTIFF:\n  {proc_tif_file}")
    with rasterio.open(
        proc_tif_file,
        "w",
        driver="GTiff",
        height=nrows,
        width=ncols,
        count=1,
        dtype=data.dtype,
        crs=f"EPSG:{publish_crs}",
        transform=transform,
        nodata=nodata,
        compress="deflate"
    ) as dst:
        dst.write(data, 1)

    # Save manifest
    proc_manifest = {
        "dataset": {
            "name": "GLiM",
            "description": "GLiM global lithology dataset prepared for GeoNinja lookup",
            "format": "geotiff",
            "geometry": "raster",
            "crs": f"EPSG:{publish_crs}",
        },
        "source": {
            "origin": src_yaml.get("full_name", ""),
            "citation": src_yaml.get("citation", ""),
            "publisher": src_yaml.get("publisher", ""),
            "license": src_yaml.get("license", ""),
            "url": src_yaml.get("url", ""),
        },
        "processing": {
            "pipeline_step": "dp_glim",
            "action": "convert",
            "from": glim_asc_file.as_posix(),
            "to": tar_tif_file.as_posix(),
            "modifications": "converted from ASCII grid to GeoTIFF with rasterio",
        },
        "intended_use": {
            "application": "GeoNinja backend",
            "usage": "Raster sample-at-point lookup for lithology",
        },
        "generated": {
            "by": "geoninja data pipeline",
            "date": date.today().isoformat(),
        },
    }
    proc_mani_file.write_text(yaml.dump(proc_manifest), encoding="utf-8")
    os.remove(glim_asc_file)

def _stage() -> None:
    # Copy process GeoTIFF, Classnames, and manifest to backend data dir
    print(
        f"[info] Staging processed data to backend data directory:\n"
        f"{tar_tif_file}\n  {tar_txt_file}\n  {tar_mani_file}"
    )
    shutil.copyfile(proc_tif_file, tar_tif_file)
    shutil.copyfile(glim_txt_file, tar_txt_file)
    shutil.copyfile(proc_mani_file, tar_mani_file)
    os.remove(proc_tif_file)
    os.remove(proc_mani_file)
    os.remove(glim_txt_file)
