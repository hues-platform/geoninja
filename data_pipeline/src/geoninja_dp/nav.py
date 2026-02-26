import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DP_DIR = REPO_ROOT / "data_pipeline"
DATA_SOURCES_DIR = DP_DIR / "sources"
BACKEND_DATA_DIR = REPO_ROOT / "backend" / "data"
IS_CONTAINER = os.getenv("GEONINJA_RUNTIME") == "container"
_DP_WORK_DIR = DP_DIR / "work"
if IS_CONTAINER:
    _DP_WORK_DIR = Path(os.getenv("GEONINJA_DP_WORK_DIR"))
    

def get_dp_work_dir() -> Path:
    """Get the path to the data pipeline work directory, and create it if it does not exist.
    This directory is loated on a named volume when running in the container, and inside the repo otherwise.
    It is used for computationally heavy operations during pipeline execution."""
    os.mkdir(_DP_WORK_DIR, exist_ok=True)
    return _DP_WORK_DIR
