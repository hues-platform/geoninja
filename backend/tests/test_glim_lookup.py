import pytest

from geoninja_backend.services.glim_lookup import GlimLithoKey, GlimLookupResult, load_glim_gdf, lookup_glim_at


@pytest.mark.glim
def test_coordinates_for_valid_location_return_lithology():
    lat = 47.4
    lon = 8.5
    result = lookup_glim_at(lat, lon)
    assert result is not None
    assert isinstance(result, GlimLookupResult)
    assert result.litho_key == GlimLithoKey.UNCONSOLIDATED_SEDIMENTS
    assert result.hit is True


@pytest.mark.glim
def test_coordinates_over_water_return_none():
    # Mid Pacific Ocean
    lat = 0.0
    lon = -140.0

    result = lookup_glim_at(lat, lon)
    assert result.litho_key is None
    assert result.hit is False


@pytest.mark.glim
def test_invalid_coordinates_raise_value_error():
    # Invalid latitude
    with pytest.raises(ValueError):
        lookup_glim_at(95.0, 8.5)

    # Invalid longitude
    with pytest.raises(ValueError):
        lookup_glim_at(47.0, 200.0)


@pytest.mark.glim
def test_glim_lithology_keys_are_covered_by_enum():
    gdf = load_glim_gdf()

    # Because we converted to category during load
    dataset_keys = set(gdf["litho_key"].cat.categories)

    enum_keys = {item.value for item in GlimLithoKey}

    missing_in_enum = dataset_keys - enum_keys
    extra_in_enum = enum_keys - dataset_keys

    assert not missing_in_enum, (
        "GLiM dataset contains lithology keys not covered by GlimLithoKey enum: " f"{sorted(missing_in_enum)}"
    )

    # Optional but useful: detect dead enum entries
    assert not extra_in_enum, "GlimLithoKey enum contains keys not present in GLiM dataset: " f"{sorted(extra_in_enum)}"
