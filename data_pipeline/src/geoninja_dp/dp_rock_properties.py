import shutil
from datetime import date
from pathlib import Path

import yaml

from geoninja_dp import __version__, nav


def run(force: bool) -> None:

    # Destination paths
    bck_data_dir = nav.BACKEND_DATA_DIR
    mani_path = bck_data_dir / "rock_properties.manifest.yaml"
    rp_tar_path = bck_data_dir / "rock_properties.csv"

    # Skip if output exists and not forced
    if mani_path.exists() and rp_tar_path.exists() and not force:
        print("[skip] Outputs already exist. Use --force to rebuild.")
        return

    # Source yaml
    src_yaml_path = nav.DATA_SOURCES_DIR / "rock_properties" / "source.yaml"
    if not src_yaml_path.exists():
        raise FileNotFoundError(f"Missing source config: {src_yaml_path}")
    src_yaml = yaml.safe_load(src_yaml_path.read_text(encoding="utf-8")) or {} 
    
    # Rock properties source file
    try:
        rp_src_path_str = src_yaml["files"]["csv"]
    except Exception as e:
        raise KeyError(
            "source.yaml must contain:\n"
            "files:\n"
            "  csv: <path-to-csv>\n"
        ) from e
    rp_src_path = Path(rp_src_path_str).absolute()
    if not rp_src_path.exists():
        raise FileNotFoundError(f"Missing rock properties source file: {rp_src_path}")

    # Copy rock properties CSV to backend data directory
    shutil.copyfile(rp_src_path, rp_tar_path)

    # Manifest
    mni = _manifest(rp_src_path, rp_tar_path)
    mani_path.write_text(yaml.dump(mni), encoding="utf-8")
    print(f"[ok] Copied rock properties CSV:\n  {rp_src_path}\n  -> {rp_tar_path}")


def _manifest(rp_src_path: Path, rp_tar_path: Path) -> dict:
    return {
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
            "input_file": rp_src_path.as_posix(),
        },
        "processing": {
            "pipeline_step": "dp_rock_properties",
            "action": "copy",
            "from": rp_src_path.as_posix(),
            "to": rp_tar_path.as_posix(),
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
