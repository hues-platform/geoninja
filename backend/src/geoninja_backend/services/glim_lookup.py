"""GLiM local lookup service.

This module provides a cached point-in-polygon lookup into the GLiM (Global
Lithological Map) dataset.

Data source
-----------
The TIF file is produced/staged by the data pipeline step
``data_pipeline.scripts.dp_glim`` and is expected at:

    ``backend/data/glim.tif``

Coordinate reference system
---------------------------
Lookups are performed in EPSG:4326 (lat/lng in degrees). If the dataset is stored
in a different CRS, it is reprojected on load.

Caching
-------
The raster dataset handle is cached via ``lru_cache(maxsize=1)`` for performance.
Rasterio dataset reads are not guaranteed to be thread-safe, so sampling is
serialized with a module-level lock.
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from threading import Lock

import numpy as np
import rasterio
from pyproj import CRS, Transformer

log = logging.getLogger(__name__)

_GLIM_FILE = (Path(__file__).parents[3] / "data" / "glim.tif").resolve()
_EXPECTED_CRS = CRS.from_epsg(4326)

# Rasterio dataset reads are not guaranteed thread-safe across workers/threads.
# Serialize reads on the cached dataset handle.
_DS_READ_LOCK = Lock()


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


_GLIM_VALUE_TO_KEY: dict[int, GlimLithoKey] = {
    1: GlimLithoKey.UNCONSOLIDATED_SEDIMENTS,  # su
    2: GlimLithoKey.BASIC_VOLCANIC_ROCKS,  # vb
    3: GlimLithoKey.SILICICLASTIC_SEDIMENTARY_ROCKS,  # ss
    4: GlimLithoKey.BASIC_PLUTONIC_ROCKS,  # pb
    5: GlimLithoKey.MIXED_SEDIMENTARY_ROCKS,  # sm
    6: GlimLithoKey.CARBONATE_SEDIMENTARY_ROCKS,  # sc
    7: GlimLithoKey.ACID_VOLCANIC_ROCKS,  # va
    8: GlimLithoKey.METAMORPHITES,  # mt
    9: GlimLithoKey.ACID_PLUTONIC_ROCKS,  # pa
    10: GlimLithoKey.INTERMEDIATE_VOLCANIC_ROCKS,  # vi
    11: GlimLithoKey.WATER_BODIES,  # wb
    12: GlimLithoKey.PYROCLASTICS,  # py
    13: GlimLithoKey.INTERMEDIATE_PLUTONIC_ROCKS,  # pi
    14: GlimLithoKey.EVAPORITES,  # ev
    15: GlimLithoKey.NO_DATA,  # nd
    16: GlimLithoKey.ICE_AND_GLACIERS,  # ig
}


def lookup_glim_at(lat: float, lng: float) -> GlimLookupResult:
    """Lookup lithology at given latitude and longitude using GLiM data."""
    # Sanity check
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        log.critical("Invalid lat/lng: (%f, %f)", lat, lng)
        raise ValueError(f"Invalid lat/lng: ({lat}, {lng})")

    # Load GLiM data (at most once due to caching)
    ds, nodata, transformer = load_glim_data()

    # Rasterio expects (x, y) in the dataset CRS. Our API is (lat, lng) in EPSG:4326, so transform if needed.
    x, y = lng, lat
    if transformer is not None:
        x, y = transformer.transform(x, y)

    # Quick reject: outside raster bounds means no hit
    if not (ds.bounds.left <= x <= ds.bounds.right and ds.bounds.bottom <= y <= ds.bounds.top):
        return GlimLookupResult(litho_key=None, hit=False)

    # Sample band 1
    with _DS_READ_LOCK:
        val_arr = next(ds.sample([(x, y)], indexes=1))

    # Convert to scalar
    val = val_arr[0]
    if val is None:
        return GlimLookupResult(litho_key=None, hit=False)

    # Handle nodata / masked values
    if nodata is not None and np.isfinite(val) and val == nodata:
        return GlimLookupResult(litho_key=None, hit=False)

    # If dtype is float, it might carry nodata as nan
    try:
        if np.isnan(val):
            return GlimLookupResult(litho_key=None, hit=False)
    except TypeError:
        # Not a float type, ignore
        pass

    # Map raster class -> litho key
    try:
        ival = int(val)
    except Exception:
        return GlimLookupResult(litho_key=None, hit=False)

    litho = _GLIM_VALUE_TO_KEY.get(ival)
    if litho is None or litho == GlimLithoKey.NO_DATA:
        return GlimLookupResult(litho_key=None, hit=False)

    return GlimLookupResult(litho_key=litho, hit=True)


@lru_cache(maxsize=1)
def load_glim_data() -> tuple[rasterio.io.DatasetReader, float | int | None, Transformer | None]:
    if not _GLIM_FILE.exists():
        log.critical("GLiM file not found at %s", _GLIM_FILE)
        raise FileNotFoundError(f"GLiM file not found at {_GLIM_FILE}")

    log.info("Loading GLiM lithology map from %s", _GLIM_FILE)
    t0 = time.time()

    ds = rasterio.open(_GLIM_FILE)
    if ds.count < 1:
        ds.close()
        raise RuntimeError(f"GLiM dataset has no bands: {_GLIM_FILE}")

    nodata = ds.nodata
    ds_crs = CRS.from_user_input(ds.crs) if ds.crs else None
    if ds_crs is None:
        log.warning("GLiM dataset has no CRS; assuming EPSG:4326")
        transformer = None
    elif ds_crs != _EXPECTED_CRS:
        log.info("GLiM dataset CRS %s differs from expected %s; building transformer", ds_crs, _EXPECTED_CRS)
        transformer = Transformer.from_crs(_EXPECTED_CRS, ds_crs, always_xy=True)
    else:
        transformer = None

    log.info("GLIM lithology map loaded in %.2f seconds", time.time() - t0)
    return ds, nodata, transformer
