import shutil
from datetime import date
from pathlib import Path

import rasterio
import yaml

from geoninja_dp import nav

# Paths
src_yml_file = nav.DATA_SOURCES_DIR / "hydr_grad" / "source.yaml"
src_tif_file = nav.DATA_SOURCES_DIR / "hydr_grad" / "hydr_grad_ger.tif"
src_tif_aux_xml_file = nav.DATA_SOURCES_DIR / "hydr_grad" / "hydr_grad_ger.tif.aux.xml"
tar_tif_file = nav.BACKEND_DATA_DIR / "hydr_grad_ger.tif"
tar_tif_aux_xml_file = nav.BACKEND_DATA_DIR / "hydr_grad_ger.tif.aux.xml"
tar_mani_file = nav.BACKEND_DATA_DIR / "hydr_grad_ger.manifest.yaml"

def run(force: bool) -> None:
    # Skip if output exists and not forced
    if tar_tif_file.exists() and tar_mani_file.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    # Source yaml
    if not src_yml_file.exists():
        raise FileNotFoundError(f"Missing source config: {src_yml_file}")
    src_yml = yaml.safe_load(src_yml_file.read_text(encoding="utf-8")) or {}

    # Pipeline steps
    _stage(src_yml, force)


def _stage(src_yml: dict, force: bool) -> None:
    # Skip if output exists and not forced
    if tar_tif_file.exists() and tar_mani_file.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    # Read raster metadata via rasterio
    with rasterio.open(src_tif_file) as ds:
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
        band1 = ds.read(1, masked=True)
        # Convert to python scalars for JSON
        data_min = float(band1.min()) if band1.count() > 0 else None
        data_max = float(band1.max()) if band1.count() > 0 else None
        valid_fraction = float(band1.count() / (width * height)) if width and height else None

    # Copy source files to backend data dir
    print(f"[info] Copying GeoTIFF:\n  {src_tif_file}\n  -> {tar_tif_file}")
    shutil.copyfile(src_tif_file, tar_tif_file)
    print(f"[info] Copying GDAL aux XML:\n  {src_tif_aux_xml_file}\n  -> {tar_tif_aux_xml_file}")
    shutil.copyfile(src_tif_aux_xml_file, tar_tif_aux_xml_file)

    # Manifest
    input_files = []
    for _, fi in src_yml.get("files").items():
        input_files.append(Path(fi).as_posix())
    manifest = {
        "dataset": {
            "name": src_yml.get("dataset", "HYDR_GRAD_GER"),
            "description": "Hydraulic gradient raster prepared for GeoNinja lookup",
            "format": "geotiff",
            "data_type": "raster",
            "bands": count,
            "dtype": dtype,
            "crs": crs or src_yml.get("crs", ""),
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
                "crs": crs or src_yml.get("crs", ""),
            },
            "nodata": nodata if nodata is not None else src_yml.get("nodata", None),
            "value_range": {"min": data_min, "max": data_max},
            "valid_fraction": valid_fraction,
            "quantity": src_yml.get("quantity", "hydraulic_gradient"),
            "stored_unit": src_yml.get("stored_unit", "percent"),
            "scale_factor_to_dimensionless": src_yml.get("scale_factor_to_dimensionless", 0.01),
            "notes": "Values assumed to be percent slope (%). Convert to dimensionless by * 0.01 before Darcy law.",
        },
        "source": {
            "origin": src_yml.get("full_name", ""),
            "citation": src_yml.get("citation", ""),
            "publisher": src_yml.get("publisher", ""),
            "url": src_yml.get("url", ""),
            "license_note": src_yml.get("license_note", ""),
            "input_files": input_files,
        },
        "processing": {
            "pipeline_step": "dp_hydraulic_gradient",
            "action": "copy",
            "from": src_tif_file.as_posix(),
            "to": tar_tif_file.as_posix(),
            "modifications": (
                "no reprojection; keep EPSG:3857; "
                "assume stored values are percent; provide scale_factor_to_dimensionless=0.01"
            ),
        },
        "intended_use": {
            "application": "GeoNinja backend",
            "usage": (
                "Raster sample-at-point lookup for hydraulic gradient; "
                "convert to dimensionless; compute v = K * i"
            ),
        },
        "generated": {
            "by": "geoninja data pipeline",
            "date": date.today().isoformat(),
        },
    }
    tar_mani_file.write_text(yaml.dump(manifest, sort_keys=False), encoding="utf-8")
    print(f"[info] Wrote manifest:\n  {tar_mani_file}")
