"""Temperature-based heating/cooling period segmentation.

This module derives representative annual heating and cooling periods from
hourly outdoor air temperature data at a given geographic location.

The segmentation follows a three-stage process:

1. Hourly classification
   Each hourly temperature value is classified as:
       - "heat"    if T < heat threshold
       - "cool"    if T > cool threshold
       - "neutral" otherwise

2. Daily aggregation
   Each calendar day of the year is classified by majority vote of its
   hourly classes. Days with no data default to "neutral".

3. Daily smoothing
   The daily class sequence is smoothed using a centered rolling window
   majority vote over several days (e.g., 7-day window). This reduces
   short-lived weather fluctuations (e.g., brief cold or warm spells)
   and yields more climatologically representative seasonal boundaries.
   Ties are resolved conservatively in favor of "neutral" or by
   preserving the original daily class.


4. Season extraction
   Contiguous runs of days matching the target class ("heat" or "cool")
   are detected. Short gaps (≤ max_gap_days) are merged to produce a
   single dominant seasonal period. Periods shorter than a configurable
   minimum duration are discarded. The longest remaining period is returned.

The result is at most one heating period and one cooling period per year.

Units and conventions
---------------------
- Temperature: degrees Celsius (°C)
- Time resolution: hourly
- Calendar basis: Gregorian year (Jan 1 – Dec 31)
- Returned dates are formatted as "DD.MM"

Scientific scope and limitations
---------------------------------
This approach is purely threshold-based and climatological. It does not
account for:
- Building-specific heating/cooling balance points
- Degree-day integration
- Internal gains or occupancy effects
- Dynamic control strategies

The derived periods therefore represent climatological operating seasons,
not optimized building operation schedules.
"""

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

from geoninja_backend.models.common import TimePeriod
from geoninja_backend.services.temp_lookup import fetch_hourly_temp

log = logging.getLogger(__name__)

OperClass = Literal["heat", "cool", "neutral"]


@dataclass(frozen=True, slots=True)
class PeriodSegmentationResult:
    """Result for period segmentation."""

    heat_period_start: str | None
    heat_period_end: str | None
    cool_period_start: str | None
    cool_period_end: str | None
    ok: bool


def perform_period_seg(lat: float, lng: float, year: int) -> PeriodSegmentationResult:
    """
    Derive representative heating and cooling periods for a given location and year.

    Parameters
    ----------
    lat : float
        Latitude in WGS84 degrees.
    lng : float
        Longitude in WGS84 degrees.
    year : int
        Calendar year for which hourly temperature data is evaluated.

    Returns
    -------
    PeriodSegmentationResult
        Dataclass containing start/end dates (formatted "DD.MM")
        for the dominant heating and cooling periods. If temperature
        data retrieval fails, `ok` is False and all fields are None.

    Notes
    -----
    Heating is assumed when hourly temperature is below 16 °C.
    Cooling is assumed when hourly temperature exceeds 23 °C.

    These thresholds are heuristic and represent typical
    comfort-based switching points rather than building-specific
    balance temperatures.
    """
    try:
        temp_data = fetch_hourly_temp(lat, lng, year)
    except Exception as e:
        log.exception(f"Failed to fetch temperature data for period segmentation. Error: {e}")
        return PeriodSegmentationResult(None, None, None, None, ok=False)

    temp_thresh_heat = 16  # Heating when temperature below this
    temp_thresh_cool = 23  # Cooling when temperature above this

    # Classify each day
    daily_class = _classify_daily(temp_data, temp_thresh_heat, temp_thresh_cool)
    daily_class = _smooth_daily_class(daily_class, window_days=7)

    # Extract seasons
    heat_period = _extract_season(daily_class, target="heat", max_gap_days=7)
    cool_period = _extract_season(daily_class, target="cool", max_gap_days=14, exclude=heat_period)

    # Return
    return PeriodSegmentationResult(
        heat_period_start=heat_period.start.strftime("%d.%m") if heat_period else None,
        heat_period_end=heat_period.end.strftime("%d.%m") if heat_period else None,
        cool_period_start=cool_period.start.strftime("%d.%m") if cool_period else None,
        cool_period_end=cool_period.end.strftime("%d.%m") if cool_period else None,
        ok=True,
    )


def _extract_season(
    daily_class: dict[date, OperClass],
    target: OperClass,
    max_gap_days: int,
    exclude: TimePeriod | None = None,
) -> TimePeriod | None:
    """
    Extract the dominant seasonal period for a target operating class.

    The function identifies contiguous runs of days classified as the
    specified target ("heat" or "cool"). Short gaps between runs are
    merged if their duration does not exceed `max_gap_days`.

    Parameters
    ----------
    daily_class : dict[date, OperClass]
        Mapping from calendar date to daily operating classification.
        Must contain a complete calendar year.
    target : OperClass
        Target classification to extract ("heat" or "cool").
    max_gap_days : int
        Maximum number of consecutive non-target days allowed between
        runs to merge them into a single season.
    exclude : TimePeriod | None, optional
        If provided, days within this period are ignored when extracting
        the season (used to prevent overlap between heating and cooling).

    Returns
    -------
    TimePeriod | None
        The longest merged seasonal period satisfying the duration
        constraint, or None if no suitable period exists.

    Notes
    -----
    Period merging accounts for year wrap-around via modulo indexing.
    """
    if not daily_class:
        return None

    # Create boolean mask of the year
    is_target: dict[date, bool] = {}
    for day in sorted(daily_class):
        oper_class = daily_class[day]
        if exclude and exclude.contains(day):
            is_target[day] = False
            continue
        is_target[day] = oper_class == target
    if not any(is_target.values()):
        return None

    # Find initial runs of target class
    runs: list[TimePeriod] = []
    in_run = False
    for curr_day in sorted(is_target):
        active = is_target[curr_day]
        if active and not in_run:
            in_run = True
            run_start = curr_day
        elif not active and in_run:
            in_run = False
            prev_day = curr_day - timedelta(days=1)
            runs.append(TimePeriod(start=run_start, end=prev_day))
    if in_run:
        last_day = date(next(iter(daily_class)).year, 12, 31)
        runs.append(TimePeriod(start=run_start, end=last_day))
    if not runs:
        return None

    # Join periods by filling gaps below max_gap_days
    still_merging = True
    while still_merging:
        still_merging = False
        new_runs = []
        skip_next = False

        count = len(runs)
        if count == 1:
            break
        for ir in range(count):
            if skip_next:
                skip_next = False
                continue
            curr_period = runs[ir]
            next_ir = (ir + 1) % count
            next_period = runs[next_ir]

            # Calculate gap
            gap_period = TimePeriod(start=curr_period.end, end=next_period.start)
            gap = gap_period.duration_days() - 2

            # Determine whether to merge with next period
            if gap <= max_gap_days:  # Merge
                new_period = TimePeriod(start=curr_period.start, end=next_period.end)
                new_runs.append(new_period)
                if gap == 0:  # Found wrap-around period
                    new_runs.pop(0)
                skip_next = True
                still_merging = True
            else:  # No merge
                new_runs.append(curr_period)

        # Update runs for new iteration
        runs = new_runs

    # Select longest run and return
    best_run = max(runs, key=lambda r: r.duration_days())
    return best_run


def _smooth_daily_class(
    daily_class: dict[date, OperClass],
    window_days: int,
) -> dict[date, OperClass]:
    """
    Smooth daily operating classes using a centered rolling majority vote.

    For each day, the class is replaced by the most frequent label in a window
    of surrounding days (inclusive). This reduces day-to-day noise (e.g., brief
    cold fronts) while preserving the overall seasonal structure.

    Parameters
    ----------
    daily_class : dict[date, OperClass]
        Mapping from day to daily class. Expected to contain a complete year.
    window_days : int
        Size of the centered smoothing window in days. Must be odd and >= 1.

    Returns
    -------
    dict[date, OperClass]
        Smoothed daily class mapping.

    Notes
    -----
    Tie-breaking:
    - Prefer "neutral" if it participates in a tie for the maximum count.
    - Otherwise fall back to the original (unsmoothed) class for that day.
    """
    if not daily_class:
        return {}

    if window_days < 1 or window_days % 2 == 0:
        raise ValueError("window_days must be an odd integer >= 1")

    days = sorted(daily_class)
    half = window_days // 2

    out: dict[date, OperClass] = {}

    for i, day in enumerate(days):
        left = max(0, i - half)
        right = min(len(days), i + half + 1)
        window_vals = [daily_class[d] for d in days[left:right]]

        c = Counter(window_vals)
        max_count = max(c.values())
        top = [cls for cls, cnt in c.items() if cnt == max_count]

        if len(top) == 1:
            out[day] = top[0]  # type: ignore[assignment]
            continue

        # Tie-break: prefer neutral (conservative smoothing)
        if "neutral" in top:
            out[day] = "neutral"
            continue

        # Final tie-break: keep original label for stability
        out[day] = daily_class[day]

    return out


def _classify_daily(
    temp_data: dict[datetime, float],
    thresh_heat: float,
    thresh_cool: float,
) -> dict[date, OperClass]:
    """
    Classify each calendar day of the year into heat/cool/neutral.

    Hourly temperature values are first classified individually, then
    aggregated by day using a majority rule:

        - If neutral hours dominate → day = "neutral"
        - Otherwise:
            "heat" if heating hours ≥ cooling hours
            "cool" otherwise

    Parameters
    ----------
    temp_data : dict[datetime, float]
        Hourly temperature time series for a single year.
    thresh_heat : float
        Heating threshold (°C).
    thresh_cool : float
        Cooling threshold (°C).

    Returns
    -------
    dict[date, OperClass]
        Mapping of every calendar day in the year to its operating class.

    Notes
    -----
    Missing days are classified as "neutral".
    """
    # Bucket hours by date
    year = list(temp_data.keys())[0].year if temp_data else 2001
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    all_days = [year_start + timedelta(days=i) for i in range((year_end - year_start).days + 1)]
    daily_buckets: dict[date, list[OperClass]] = {day: [] for day in all_days}
    for dt, temp in temp_data.items():
        daily_buckets[dt.date()].append(_classify_hour(temp, thresh_heat, thresh_cool))

    # Classify each day by majority logic
    daily_class: dict[date, OperClass] = {}
    for day, daily_temps in daily_buckets.items():
        if not daily_temps:
            daily_class[day] = "neutral"
            continue
        c = Counter(daily_temps)
        n_heat = c.get("heat", 0)
        n_cool = c.get("cool", 0)
        n_neut = c.get("neutral", 0)

        if n_neut > n_heat and n_neut > n_cool:
            daily_class[day] = "neutral"
        else:
            daily_class[day] = "heat" if n_heat >= n_cool else "cool"

    return daily_class


def _classify_hour(temp: float, thresh_heat: float, thresh_cool: float) -> OperClass:
    """
    Classify a single hourly temperature value.

    Parameters
    ----------
    temp : float
        Outdoor air temperature (°C).
    thresh_heat : float
        Heating threshold (°C).
    thresh_cool : float
        Cooling threshold (°C).

    Returns
    -------
    OperClass
        "heat", "cool", or "neutral".
    """
    if temp < thresh_heat:
        return "heat"
    if temp > thresh_cool:
        return "cool"
    return "neutral"
