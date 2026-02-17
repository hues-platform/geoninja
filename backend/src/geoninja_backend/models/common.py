"""Common/shared models.

This module contains small, reusable types used across API models and services.
"""

from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, ConfigDict


class LatLng(BaseModel):
    """Geographic coordinates.

    This type is used in API requests/responses where a location must be
    provided by the client.

    Attributes:
        lat: Latitude in decimal degrees.
        lng: Longitude in decimal degrees.
    """

    model_config = ConfigDict(extra="forbid")
    lat: float
    lng: float


@dataclass(frozen=True, slots=True)
class TimePeriod:
    """A date range within a single calendar year.

    The period can be either:

    - **Joint** (non-wrapping): ``start <= end`` (e.g., 2026-03-01 .. 2026-04-15)
    - **Wrapping** (across year boundary): ``start > end`` meaning the range wraps
      around New Year's Eve (e.g., 2026-10-01 .. 2026-03-30)

    In the wrapping case, :meth:`contains` treats the period as
    ``[start .. Dec 31] U [Jan 1 .. end]`` for the given year.

    Raises:
        ValueError: If ``start`` and ``end`` are not in the same year.
    """

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start.year != self.end.year:
            raise ValueError("TimePeriod start and end must be in the same year")

    @property
    def year(self) -> int:
        return self.start.year

    @property
    def is_joint(self) -> bool:
        return self.start <= self.end

    def contains(self, d: date) -> bool:
        if d.year != self.year:
            return False
        if self.is_joint:
            return self.start <= d <= self.end
        return d >= self.start or d <= self.end

    def duration_days(self) -> int:
        if self.is_joint:
            return (self.end - self.start).days + 1

        year_end = date(self.year, 12, 31)
        year_start = date(self.year, 1, 1)

        days_tail = (year_end - self.start).days + 1  # start..Dec31 inclusive
        days_head = (self.end - year_start).days + 1  # Jan1..end inclusive
        return days_tail + days_head

    def duration_secs(self) -> int:
        return self.duration_days() * 24 * 3600
