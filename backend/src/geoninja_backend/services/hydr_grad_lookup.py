"""Hydraulic gradient raster lookup service.

This module provides a cached sample-at-point lookup into the hydraulic gradient
raster used by the local parameter lookup endpoint.

Data source
-----------
The GeoTIFF is staged by the data pipeline step
``data_pipeline.scripts.dp_hydr_grad`` and is expected at:

    ``backend/data/hydr_grad_ger.tif``

Coordinate reference system
---------------------------
Clients query in EPSG:4326 (lat/lng in degrees). The raster itself is expected to
be in EPSG:3857. The lookup transforms the query point into raster coordinates
and samples the nearest pixel.

Units
-----
Raster values are assumed to be stored as *percent* slope (e.g., 5 means 5%).
The lookup converts to a dimensionless hydraulic gradient by dividing by 100.

Caching
--------
The raster dataset handle is cached via ``lru_cache(maxsize=1)`` for performance.
Rasterio dataset reads are not guaranteed to be thread-safe, so sampling is
serialized with a module-level lock.
"""

import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from threading import Lock

import rasterio  # type: ignore[import-untyped]
from pyproj import CRS, Transformer

log = logging.getLogger(__name__)

_HYDRGRAD_GER_FILE = (Path(__file__).parents[3] / "data" / "hydr_grad_ger.tif").resolve()

_EXPECTED_RASTER_CRS = CRS.from_epsg(3857)
_INPUT_CRS = CRS.from_epsg(4326)

# Rasterio dataset reads are not guaranteed thread-safe across workers/threads.
# Serialize reads on the cached dataset handle.
_DS_READ_LOCK = Lock()


@dataclass(frozen=True, slots=True)
class HydrGradLookupResult:
    """Result for a hydraulic-gradient raster lookup.

    Attributes:
        hydr_grad: Dimensionless gradient (e.g., 0.05 for 5%), or ``None`` if the
            point is outside raster bounds or maps to NoData.
        hit: ``True`` if a valid raster cell was sampled.
    """

    hydr_grad: float | None
    hit: bool


def lookup_hydr_grad_at(lat: float, lng: float) -> HydrGradLookupResult:
    """Lookup hydraulic gradient at given latitude and longitude using hydr_grad_ger raster.

    Parameters
    ----------
    lat : float
        Latitude in degrees (EPSG:4326).
    lng : float
        Longitude in degrees (EPSG:4326).

    Returns
    -------
    HydrGradLookupResult
        Result containing a dimensionless hydraulic gradient and a hit flag.

    Raises
    ------
    ValueError
        If latitude/longitude are outside valid ranges.
    FileNotFoundError
        If the raster file is missing.
    ValueError
        If the raster CRS is missing or unexpected.
    """
    # Sanity check
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        log.critical("Invalid lat/lng: (%f, %f)", lat, lng)
        raise ValueError(f"Invalid lat/lng: ({lat}, {lng})")

    ds, to_raster = load_hydr_grad_raster()

    # Transform WGS84 lat/lon -> raster CRS (EPSG:3857)
    x, y = to_raster.transform(lng, lat)  # Transformer expects (x,y) = (lon,lat)

    # Quick bounds check (prevents Rasterio errors + faster miss)
    b = ds.bounds
    if x < b.left or x > b.right or y < b.bottom or y > b.top:
        return HydrGradLookupResult(None, False)

    # Sample nearest pixel at (x,y) in raster CRS
    with _DS_READ_LOCK:
        # ds.sample returns an iterator of arrays (one per point)
        v = next(ds.sample([(x, y)]))[0]

    # Handle NoData / NaN
    nodata = ds.nodata
    if nodata is not None and v == nodata:
        return HydrGradLookupResult(None, False)

    # Some rasters use NaN as nodata; v could be numpy.float32
    try:
        if v != v:  # NaN check without importing numpy
            return HydrGradLookupResult(None, False)
    except Exception:
        pass

    # Transform percent to dimensionless
    v = float(v) / 100.0

    return HydrGradLookupResult(v, True)


@lru_cache(maxsize=1)
def load_hydr_grad_raster():
    """Load the hydraulic gradient raster once and return (dataset, transformer).

    Returns:
        A tuple ``(ds, to_raster)`` where:
        - ``ds`` is an open Rasterio dataset for the GeoTIFF
        - ``to_raster`` transforms EPSG:4326 (lon/lat) into EPSG:3857 (x/y)

    Notes:
        The open dataset handle is cached at process level. Callers should not
        close the returned dataset.
    """
    if not _HYDRGRAD_GER_FILE.exists():
        log.critical("HydrGrad GER raster not found at %s", _HYDRGRAD_GER_FILE)
        raise FileNotFoundError(f"HydrGrad GER raster not found at {_HYDRGRAD_GER_FILE}")

    log.info("Loading HydrGrad GER raster from %s", _HYDRGRAD_GER_FILE)
    t0 = time.time()

    ds = rasterio.open(_HYDRGRAD_GER_FILE)

    if ds.crs is None:
        ds.close()
        log.critical("No CRS found in hydr_grad_ger raster")
        raise ValueError("No CRS found in hydr_grad_ger raster")
    if not CRS.from_user_input(ds.crs).equals(_EXPECTED_RASTER_CRS):
        # We could support any CRS via transformer, but for your stack it’s better to fail loudly.
        ds.close()
        log.critical(
            "Unexpected CRS in hydr_grad_ger raster: %s (expected %s)",
            ds.crs,
            _EXPECTED_RASTER_CRS,
        )
        raise ValueError(f"Unexpected CRS in hydr_grad_ger raster: {ds.crs} (expected EPSG:3857)")
    # Basic sanity: single band raster expected
    if ds.count < 1:
        ds.close()
        log.critical("hydr_grad_ger raster has no bands")
        raise ValueError("hydr_grad_ger raster has no bands")

    # Pre-build transformer (lon/lat -> raster CRS)
    to_raster = Transformer.from_crs(_INPUT_CRS, _EXPECTED_RASTER_CRS, always_xy=True)

    log.info(
        "HydrGrad GER raster loaded in %.2f seconds from {%s}",
        time.time() - t0,
        _HYDRGRAD_GER_FILE,
    )

    return ds, to_raster
