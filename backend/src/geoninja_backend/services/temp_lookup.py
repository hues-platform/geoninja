"""Hourly outdoor temperature lookup via Open-Meteo archive API.

This module provides a small helper to obtain historical near-surface air
temperature time series for a given point location and year. It is intended to
support period segmentation (heating/cooling season detection) and other
location-dependent heuristics.

Data source
-----------
The Open-Meteo archive endpoint serves historical weather time series derived
from gridded reanalysis/forecast products (dataset choice is handled by
Open-Meteo). The API returns a fixed hourly grid in the requested timezone.

- Endpoint: https://archive-api.open-meteo.com/v1/archive
- Variable used here: ``temperature_2m`` (air temperature at 2 m above ground)

Units and conventions
---------------------
- Temperature is returned in degrees Celsius (°C) by Open-Meteo unless a
  different unit is explicitly requested.
- Time stamps are returned as ISO 8601 strings in the requested timezone
  (we request ``UTC``).

Error handling
--------------
This function raises:
- :class:`requests.HTTPError` for non-2xx responses (via ``raise_for_status``).
- :class:`RuntimeError` if the response JSON is missing expected fields or the
  returned time/value arrays are inconsistent.

Notes
-----
- This helper performs a network request and may be slow. Callers should
  consider caching results per (lat, lng, year) to avoid repeated downloads.
- The returned mapping uses naive ``datetime`` objects that represent UTC
  timestamps (because we request ``timezone=UTC``). If you prefer timezone-aware
  datetimes, convert after parsing.
"""

from datetime import datetime

import requests
from pyparsing import Mapping


def fetch_hourly_temp(lat: float, lng: float, year: int) -> dict[datetime, float]:
    """Fetch hourly 2 m air temperature for a location and year from Open-Meteo.

    Parameters
    ----------
    lat : float
        Latitude in WGS84 degrees.
    lng : float
        Longitude in WGS84 degrees.
    year : int
        Calendar year to fetch (January 1st to December 31st, inclusive).

    Returns
    -------
    dict[datetime, float]
        Mapping of hourly timestamps (UTC; naive ``datetime``) to air temperature
        at 2 m height (°C).

    Raises
    ------
    requests.HTTPError
        If the Open-Meteo API returns a non-2xx response.
    RuntimeError
        If the response JSON is missing required fields or contains inconsistent
        time/value arrays.

    Notes
    -----
    - Open-Meteo returns time stamps as ISO 8601 strings; we parse them using
      :meth:`datetime.fromisoformat`.
    - ``zip(..., strict=True)`` is used to fail fast if the API returns arrays
      of different lengths.
    """
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)

    params: Mapping[str, str | int | float] = {
        "latitude": lat,
        "longitude": lng,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m",
        "timezone": "UTC",
    }

    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time")
    temps = hourly.get("temperature_2m")

    if not times or not temps or len(times) != len(temps):
        raise RuntimeError("Malformed Open-Meteo response")

    return {datetime.fromisoformat(t): temp for t, temp in zip(times, temps, strict=True)}
