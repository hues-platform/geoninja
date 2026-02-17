from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from geoninja_backend.models.common import LatLng, TimePeriod


def test_latlng_accepts_lat_lng():
    loc = LatLng(lat=47.3769, lng=8.5417)
    assert loc.lat == pytest.approx(47.3769)
    assert loc.lng == pytest.approx(8.5417)


def test_latlng_rejects_extra_fields():
    with pytest.raises(ValidationError):
        LatLng(lat=1.0, lng=2.0, extra=123)


@pytest.mark.parametrize("payload", [{"lat": 1.0}, {"lng": 2.0}, {}])
def test_latlng_requires_both_fields(payload: dict):
    with pytest.raises(ValidationError):
        LatLng.model_validate(payload)


def test_timeperiod_rejects_cross_year_dates():
    with pytest.raises(ValueError, match="same year"):
        TimePeriod(start=date(2025, 12, 31), end=date(2026, 1, 1))


def test_timeperiod_year_property():
    tp = TimePeriod(start=date(2026, 3, 1), end=date(2026, 3, 10))
    assert tp.year == 2026


def test_timeperiod_is_joint_true_when_start_le_end():
    tp = TimePeriod(start=date(2026, 3, 1), end=date(2026, 3, 10))
    assert tp.is_joint is True


def test_timeperiod_is_joint_false_when_start_gt_end_wrapping():
    tp = TimePeriod(start=date(2026, 10, 1), end=date(2026, 3, 30))
    assert tp.is_joint is False


def test_timeperiod_contains_joint_includes_endpoints():
    tp = TimePeriod(start=date(2026, 3, 1), end=date(2026, 3, 10))
    assert tp.contains(date(2026, 3, 1)) is True
    assert tp.contains(date(2026, 3, 10)) is True
    assert tp.contains(date(2026, 2, 28)) is False
    assert tp.contains(date(2026, 3, 11)) is False


def test_timeperiod_contains_rejects_different_year():
    tp = TimePeriod(start=date(2026, 3, 1), end=date(2026, 3, 10))
    assert tp.contains(date(2025, 3, 5)) is False


def test_timeperiod_contains_wrapping_includes_tail_and_head():
    tp = TimePeriod(start=date(2026, 10, 1), end=date(2026, 3, 30))

    assert tp.contains(date(2026, 10, 1)) is True
    assert tp.contains(date(2026, 12, 31)) is True
    assert tp.contains(date(2026, 1, 1)) is True
    assert tp.contains(date(2026, 3, 30)) is True

    assert tp.contains(date(2026, 4, 1)) is False
    assert tp.contains(date(2026, 9, 30)) is False


def test_timeperiod_duration_days_joint_is_inclusive():
    tp = TimePeriod(start=date(2026, 3, 1), end=date(2026, 3, 10))
    assert tp.duration_days() == 10


def test_timeperiod_duration_days_wrapping_matches_tail_plus_head():
    tp = TimePeriod(start=date(2026, 10, 1), end=date(2026, 3, 30))

    tail_days = (date(2026, 12, 31) - date(2026, 10, 1)).days + 1
    head_days = (date(2026, 3, 30) - date(2026, 1, 1)).days + 1
    assert tp.duration_days() == tail_days + head_days


def test_timeperiod_duration_secs_is_days_times_86400():
    tp = TimePeriod(start=date(2026, 3, 1), end=date(2026, 3, 10))
    assert tp.duration_secs() == tp.duration_days() * 24 * 3600
