import pytest

from geoninja_backend.services.glhymps_lookup import GlhympsLookupResult, lookup_glhymps_at


@pytest.mark.glhymps
def test_coordinates_for_valid_location_return_data():
    lat = 47.4
    lon = 8.5
    result = lookup_glhymps_at(lat, lon)
    assert result is not None
    assert isinstance(result, GlhympsLookupResult)
    assert result.hydr_cond == pytest.approx(1.1481536214968841e-05)
    assert result.hit is True


@pytest.mark.glhymps
def test_coordinates_over_water_return_none():
    # Mid Pacific Ocean
    lat = 0.0
    lon = -140.0

    result = lookup_glhymps_at(lat, lon)
    assert result.hydr_cond is None
    assert result.hit is False


@pytest.mark.glhymps
def test_invalid_coordinates_raise_value_error():
    # Invalid latitude
    with pytest.raises(ValueError):
        lookup_glhymps_at(95.0, 8.5)

    # Invalid longitude
    with pytest.raises(ValueError):
        lookup_glhymps_at(47.0, 200.0)
