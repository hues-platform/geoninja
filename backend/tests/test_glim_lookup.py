import pytest

from geoninja_backend.services.glim_lookup import (
    _GLIM_VALUE_TO_KEY,
    GlimLithoKey,
    load_glim_data,
    lookup_glim_at,
)


@pytest.mark.glim
def test_coordinates_for_valid_location_return_lithology():
    lat = 47.4
    lon = 8.5

    result = lookup_glim_at(lat, lon)

    assert result is not None
    assert result.litho_key == GlimLithoKey.MIXED_SEDIMENTARY_ROCKS
    assert result.hit is True


@pytest.mark.glim
def test_coordinates_over_water_return_none():
    lat = 0.0
    lon = -140.0

    result = lookup_glim_at(lat, lon)

    assert result.litho_key is None
    assert result.hit is False


@pytest.mark.glim
def test_invalid_coordinates_raise_value_error():
    with pytest.raises(ValueError):
        lookup_glim_at(95.0, 8.5)

    with pytest.raises(ValueError):
        lookup_glim_at(47.0, 200.0)


@pytest.mark.glim
def test_raster_crs_is_epsg_4326():
    ds, _, _ = load_glim_data()
    assert ds.crs.to_epsg() == 4326


@pytest.mark.glim
def test_all_raster_classes_are_covered_by_enum():
    ds, nodata, _ = load_glim_data()

    # Read full raster values (small: 720x360)
    values = ds.read(1)

    unique_vals = set(int(v) for v in set(values.flatten()) if v != nodata)

    enum_vals = set(_GLIM_VALUE_TO_KEY.keys())

    missing = unique_vals - enum_vals
    extra = enum_vals - unique_vals

    assert not missing, f"Raster contains class values not mapped in enum: {missing}"
    assert not extra, f"Enum maps class values not present in raster: {extra}"
