"""GLiM local lookup service.

This module provides a cached point-in-polygon lookup into the GLiM (Global
Lithological Map) dataset.

Data source
-----------
The Parquet file is produced/staged by the data pipeline step
``data_pipeline.scripts.dp_glim`` and is expected at:

    ``backend/data/glim.parquet``

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
from enum import Enum
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point

log = logging.getLogger(__name__)

_GLIM_FILE = (Path(__file__).parents[3] / "data" / "glim.parquet").resolve()
_ROCKTYPE_COL = "litho_key"
_EXPECTED_CRS = CRS.from_epsg(4326)


class GlimLithoKey(Enum):
    """Enumeration of GLiM lithology keys.

    Values correspond to the `litho_key` column in the GLiM dataset.
    """

    EVAPORITES = "ev"
    METAMORPHITES = "mt"
    ACID_PLUTONIC_ROCKS = "pa"
    BASIC_PLUTONIC_ROCKS = "pb"
    INTERMEDIATE_PLUTONIC_ROCKS = "pi"
    PYROCLASTICS = "py"
    CARBONATE_SEDIMENTARY_ROCKS = "sc"
    MIXED_SEDIMENTARY_ROCKS = "sm"
    SILICICLASTIC_SEDIMENTARY_ROCKS = "ss"
    UNCONSOLIDATED_SEDIMENTS = "su"
    ACID_VOLCANIC_ROCKS = "va"
    BASIC_VOLCANIC_ROCKS = "vb"
    INTERMEDIATE_VOLCANIC_ROCKS = "vi"
    WATER_BODIES = "wb"
    ICE_AND_GLACIERS = "ig"
    NO_DATA = "nd"


@dataclass(frozen=True, slots=True)
class GlimLookupResult:
    """Result for a GLiM lookup.

    Attributes:
        litho_key: The resolved lithology key, or ``None`` if no polygon matched.
        hit: ``True`` if the point falls inside any GLiM polygon.
    """

    litho_key: GlimLithoKey | None
    hit: bool


def lookup_glim_at(lat: float, lng: float) -> GlimLookupResult:
    """Lookup lithology at given latitude and longitude using GLiM data.

    The lookup uses a spatial index for candidate preselection and then an exact
    geometry predicate (``contains``).

    Parameters
    ----------
    lat : float
        Latitude in degrees (EPSG:4326).
    lng : float
        Longitude in degrees (EPSG:4326).

    Returns
    -------
    GlimLookupResult
        Lookup result containing the resolved lithology key (when available) and
        a hit flag.

    Raises
    ------
    ValueError
        If latitude/longitude are outside valid ranges.
    FileNotFoundError
        If the GLiM parquet file is missing.
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
    gdf = load_glim_gdf()

    # Fast preselect with spatial index
    candidate_idx = list(gdf.sindex.intersection(point.bounds))
    if not candidate_idx:
        return GlimLookupResult(None, False)

    # Exact geometry check
    candidates = gdf.iloc[candidate_idx]
    hits = candidates[candidates.geometry.contains(point)]

    # Get first hit
    if hits.empty:
        return GlimLookupResult(None, False)
    value_str = hits.iloc[0][_ROCKTYPE_COL]
    try:
        glim_litho_key = GlimLithoKey(value_str)
    except ValueError:
        log.critical("Unknown GLiM lithology key '%s' encountered", value_str)
        raise

    # Convert to Enum and return
    try:
        return GlimLookupResult(glim_litho_key, True)
    except ValueError:
        log.critical("Unknown GLiM lithology key '%s' encountered", value_str)
        raise


@lru_cache(maxsize=1)
def load_glim_gdf() -> gpd.GeoDataFrame:
    """Load the GLiM GeoDataFrame and build its spatial index.

    Notes:
        - The returned GeoDataFrame is cached at the process level.
        - CRS is validated and normalized to EPSG:4326.
        - The spatial index is built eagerly so subsequent lookups are fast.
    """
    if not _GLIM_FILE.exists():
        log.critical("GLiM file not found at %s", _GLIM_FILE)
        raise FileNotFoundError(f"GLiM file not found at {_GLIM_FILE}")

    log.info("Loading GLiM lithology map from %s", _GLIM_FILE)
    t0 = time.time()

    gdf = gpd.read_parquet(_GLIM_FILE)
    if _ROCKTYPE_COL not in gdf.columns:
        log.critical("Expected column '%s' not found in GLiM data", _ROCKTYPE_COL)
        raise KeyError(f"Expected column '{_ROCKTYPE_COL}' not found in GLiM data")
    if gdf.crs is None:
        log.critical("No CRS found in GLiM data")
        raise ValueError("No CRS found in GLiM data")
    if not gdf.crs.equals(_EXPECTED_CRS):
        log.info("Transforming GLiM data CRS from %s to %s", gdf.crs, _EXPECTED_CRS)
        gdf = gdf.to_crs(_EXPECTED_CRS)

    # Geometry sanity
    if gdf.geometry.isna().all():
        log.critical("GLiM data contains no valid geometries (all geometries are null)")
        raise ValueError("GLiM data contains no valid geometries")

    # Memory optimization (categorical codes for repeated lithology labels)
    gdf[_ROCKTYPE_COL] = gdf[_ROCKTYPE_COL].astype("category")

    # Build spatial index
    _ = gdf.sindex

    log.info("GLIM lithology map loaded in %.2f seconds", time.time() - t0)
    return gdf
