import pytest

from geoninja_backend.services.hydr_grad_lookup import HydrGradLookupResult, load_hydr_grad_raster, lookup_hydr_grad_at


@pytest.mark.hydr_grad
def test_valid_location_in_germany_returns_value_or_nodata_but_no_crash():
    # Pick a point well inside the raster’s Germany-ish bounds (from gdalinfo center is safe).
    lat = 51.33
    lng = 10.45

    res = lookup_hydr_grad_at(lat, lng)

    assert isinstance(res, HydrGradLookupResult)

    # The dataset has nodata coverage (valid_percent ~ 65%), so allow both:
    # - hit True with a numeric value
    # - hit False (nodata) at this location
    if res.hit:
        assert isinstance(res.hydr_grad, float)
        # basic sanity: gradients shouldn't be negative
        assert res.hydr_grad >= 0.0
    else:
        assert res.hydr_grad is None


@pytest.mark.hydr_grad
def test_location_far_outside_raster_bounds_returns_miss():
    # Clearly outside Germany raster bounds
    lat = 0.0
    lng = -140.0

    res = lookup_hydr_grad_at(lat, lng)

    assert isinstance(res, HydrGradLookupResult)
    assert res.hit is False
    assert res.hydr_grad is None


@pytest.mark.hydr_grad
def test_invalid_coordinates_raise_value_error():
    with pytest.raises(ValueError):
        lookup_hydr_grad_at(95.0, 8.5)

    with pytest.raises(ValueError):
        lookup_hydr_grad_at(47.0, 200.0)


@pytest.mark.hydr_grad
def test_raster_metadata_sanity():
    ds, _ = load_hydr_grad_raster()

    # Basic assumptions for your lookup implementation
    assert ds.count >= 1
    assert ds.width > 0 and ds.height > 0
    assert ds.crs is not None
    assert ds.nodata is not None  # you expect nodata handling

    # Optional: check expected CRS EPSG:3857 if you hard-require it
    # (String compare is robust enough here)
    assert "3857" in str(ds.crs)


@pytest.mark.hydr_grad
def test_loader_is_cached():
    ds1, t1 = load_hydr_grad_raster()
    ds2, t2 = load_hydr_grad_raster()

    # lru_cache(maxsize=1) should return the same objects
    assert ds1 is ds2
    assert t1 is t2
