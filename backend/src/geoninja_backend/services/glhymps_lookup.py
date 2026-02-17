"""GLHYMPS local lookup service.

This module provides a cached point-in-polygon lookup into the GLHYMPS dataset to
resolve hydrogeologic properties at a given latitude/longitude.

Data source
-----------
The GeoParquet file is produced by the data pipeline step
``data_pipeline.scripts.dp_glhymps`` and is expected at:

    ``backend/data/glhymps.parquet``

Coordinate reference system
---------------------------
Lookups are performed in EPSG:4326 (lat/lng in degrees). If the dataset is stored
in a different CRS, it is reprojected on load.

Caching
-------
The dataset is loaded once per process using ``lru_cache(maxsize=1)``. The
FastAPI app preloads this cache at startup (see
``geoninja_backend.main.lifespan``) to keep request latency predictable.
"""

import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point

log = logging.getLogger(__name__)

_GLHYMPS_FILE = (Path(__file__).parents[3] / "data" / "glhymps.parquet").resolve()
_HYDRCOND_COL = "hydraulic_conductivity_m_s"
_POROSITY_COL = "porosity"

_EXPECTED_CRS = CRS.from_epsg(4326)


@dataclass(frozen=True, slots=True)
class GlhympsLookupResult:
    """Result for a GLHYMPS lookup."""

    hydr_cond: float | None
    hit: bool


def lookup_glhymps_at(lat: float, lng: float) -> GlhympsLookupResult:
    """Lookup hydraulic conductivity at a given location using GLHYMPS.

    The lookup uses a spatial index for candidate preselection and then an exact
    geometry predicate (``covers``).

    Parameters
    ----------
    lat : float
        Latitude in degrees (EPSG:4326).
    lng : float
        Longitude in degrees (EPSG:4326).

    Returns
    -------
    GlhympsLookupResult
        Lookup result containing the hydraulic conductivity (m/s) when available
        and a hit flag indicating whether the point is inside any polygon.

    Raises
    ------
    ValueError
        If latitude/longitude are outside valid ranges.
    FileNotFoundError
        If the GLHYMPS parquet file is missing.
    KeyError
        If required columns are missing from the dataset.
    """
    # Sanity check
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        log.critical("Invalid lat/lng: (%f, %f)", lat, lng)
        raise ValueError(f"Invalid lat/lng: ({lat}, {lng})")

    # Shapely uses (x,y) = (lng, lat)
    point = Point(lng, lat)

    # Load GLiM data (at most once due to caching)
    gdf = load_glhymps_gdf()

    # Fast preselect with spatial index
    candidate_idx = list(gdf.sindex.intersection(point.bounds))
    if not candidate_idx:
        return GlhympsLookupResult(None, False)

    # Exact geometry check
    candidates = gdf.iloc[candidate_idx]
    hits = candidates[candidates.geometry.covers(point)]

    # Get first hit and return
    if hits.empty:
        return GlhympsLookupResult(None, False)
    hydr_cond = hits.iloc[0].get(_HYDRCOND_COL, None)
    return GlhympsLookupResult(hydr_cond, True)


@lru_cache(maxsize=1)
def load_glhymps_gdf() -> gpd.GeoDataFrame:
    """Load the GLHYMPS GeoDataFrame and build its spatial index.

    Notes:
        - The returned GeoDataFrame is cached at the process level.
        - CRS is validated and normalized to EPSG:4326.
        - The spatial index is built eagerly so subsequent lookups are fast.
    """
    if not _GLHYMPS_FILE.exists():
        log.critical("GLHYMPS file not found at %s", _GLHYMPS_FILE)
        raise FileNotFoundError(f"GLHYMPS file not found at {_GLHYMPS_FILE}")

    log.info("Loading GLHMYMPS map for hydraulic conductivity and porosity from %s", _GLHYMPS_FILE)
    t0 = time.time()

    gdf = gpd.read_parquet(_GLHYMPS_FILE)
    for col in [_HYDRCOND_COL, _POROSITY_COL]:
        if col not in gdf.columns:
            log.critical("Expected column '%s' not found in GLHYMPS data", col)
            raise KeyError(f"Expected column '{col}' not found in GLHYMPS data")
    if gdf.crs is None:
        log.critical("No CRS found in GLHYMPS data")
        raise ValueError("No CRS found in GLHYMPS data")
    if not gdf.crs.equals(_EXPECTED_CRS):
        log.info("Transforming GLHYMPS data CRS from %s to %s", gdf.crs, _EXPECTED_CRS)
        gdf = gdf.to_crs(_EXPECTED_CRS)

    # Geometry sanity
    if gdf.geometry.isna().all():
        log.critical("GLHYMPS data contains no valid geometries (all geometries are null)")
        raise ValueError("GLHYMPS data contains no valid geometries")

    # Build spatial index
    _ = gdf.sindex

    log.info("GLHYMPS map loaded in %.2f seconds", time.time() - t0)
    return gdf
