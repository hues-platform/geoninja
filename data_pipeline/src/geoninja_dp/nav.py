import os
from pathlib import Path

IS_CONTAINER = os.getenv("GEONINJA_RUNTIME") == "container"

def _repo_root() -> Path:
    # In Docker: make this the single source of truth
    env = os.getenv("GEONINJA_REPO_DIR")
    if env:
        return Path(env).resolve()

    p = Path(__file__).resolve()
    # Defensive: try to find a directory containing "data_pipeline" and "backend"
    for parent in p.parents:
        if (parent / "data_pipeline").is_dir() and (parent / "backend").is_dir():
            return parent.resolve()

    # Last resort: previous behavior (may be wrong depending on install location)
    return p.parents[4].resolve()

REPO_ROOT = _repo_root()
DP_DIR = REPO_ROOT / "data_pipeline"
DATA_SOURCES_DIR = DP_DIR / "sources"
BACKEND_DATA_DIR = REPO_ROOT / "backend" / "data"

def get_dp_work_dir() -> Path:
    """Work dir for heavy pipeline ops. In container, use named volume if provided."""
    env_work = os.getenv("GEONINJA_DP_WORK_DIR")
    dp_work_dir = Path(env_work).resolve() if (IS_CONTAINER and env_work) else (DP_DIR / "work")
    dp_work_dir.mkdir(parents=True, exist_ok=True)
    return dp_work_dir
