import os
import shutil
from datetime import date

import requests
import yaml

from geoninja_dp import nav

# Paths
src_yml_file = nav.DATA_SOURCES_DIR / "hydr_grad" / "source.yaml"
work_dir = nav.get_dp_work_dir() / "hydr_grad"
cache_dir = work_dir / "_cache"
zenodo_zip_dl_file = cache_dir / "hydr_grad_zenodo.zip"
hydr_grad_tif_file = cache_dir / "hydr_grad_ger.tif"
hydr_grad_xml_file = cache_dir / "hydr_grad_ger.tif.aux.xml"
tar_mani_file = nav.BACKEND_DATA_DIR / "hydr_grad.manifest.yaml"
tar_tif_file = nav.BACKEND_DATA_DIR / "hydr_grad.tif"
tar_xml_file = nav.BACKEND_DATA_DIR / "hydr_grad.tif.aux.xml"

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
    _extract(src_yaml, force)
    _stage()

def _download(src_yaml: dict, force: bool) -> None:
    # Read Zenodo info from source yaml
    zenodo = src_yaml.get("zenodo")
    if not isinstance(zenodo, dict):
        raise KeyError(
            "source.yaml must contain:\n"
            "zenodo:\n"
            "  url: <Zenodo url>\n"
        )

    # Handle paths and folders in cache directory
    url = zenodo.get("url")
    if not url:
        raise KeyError("zenodo mapping must contain 'url'")

    if force and cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = zenodo_zip_dl_file
    if not force and zip_path.exists():
        print(f"[skip] Zenodo download already exists: {zip_path}")
        return

    # Download zip
    print(f"[info] Downloading hydraulic gradient data to {zip_path} from {url}")
    with requests.get(url, stream=True, timeout=300) as r:
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            if r.status_code in (401, 403):
                hint = (
                    "\n[hint] This dataset or some files may be restricted."
                )
            raise RuntimeError(
                f"Zenodo download failed ({r.status_code}) from {url}.{hint}"
            ) from e
        chunk_size = 1024 * 1024
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
    print(f"[ok] Downloaded hydraulic gradient data to {zip_path}")


def _extract(src_yaml: dict, force: bool) -> None:
    # Extract zip
    expected_files = [hydr_grad_tif_file, hydr_grad_xml_file]
    if not force and all(fi.exists() for fi in expected_files):
        print("[skip] Zenodo zip already extracted with expected files:")
        for fi in expected_files:
            print(f"  {fi}")
        return
    else:
        print(f"[info] Extracting hydraulic gradient data zip:\n {zenodo_zip_dl_file}")
        shutil.unpack_archive(zenodo_zip_dl_file, cache_dir)
        missing_files = [fi for fi in expected_files if not fi.exists()]
        if missing_files:
            raise FileNotFoundError(
                f"Expected files not found in Zenodo ZIP: {missing_files}"
            )
        os.remove(zenodo_zip_dl_file)

        # Save manifest
        proc_manifest = {
            "dataset": {
                "name": "Hydraulic gradient",
                "description": "Hydraulic gradient raster map for Germany.",
                "format": "geotiff",
                "geometry": "raster",
                "crs": "EPSG:3857",
            },
            "source": {
                "origin": src_yaml.get("full_name", ""),
                "citation": src_yaml.get("citation", ""),
                "license": src_yaml.get("license", ""),
                "url": src_yaml.get("url", ""),
            },
            "intended_use": {
                "application": "GeoNinja backend",
                "usage": "Raster sample-at-point lookup for hydraulic gradient",
            },
            "generated": {
                "by": "geoninja data pipeline",
                "date": date.today().isoformat(),
            },
        }
        tar_mani_file.write_text(yaml.dump(proc_manifest), encoding="utf-8")


def _stage() -> None:
    # Copy process GeoTIFF, Classnames, and manifest to backend data dir
    print(
        f"[info] Staging data to backend data directory:\n"
        f"{tar_tif_file}\n  {tar_tif_file}\n  {tar_mani_file}"
    )
    shutil.copyfile(hydr_grad_tif_file, tar_tif_file)
    shutil.copyfile(hydr_grad_xml_file, tar_xml_file)
    os.remove(hydr_grad_tif_file)
    os.remove(hydr_grad_xml_file)
