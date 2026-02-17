import math

import pytest

from geoninja_backend.core.analysis_result_registry import (
    ATES_KPI_RESULT_REGISTRY,
    DERIVED_QUANTITY_REGISTRY,
)
from geoninja_backend.services import analysis as analysis_service


def _valid_params() -> dict[str, float | str]:
    # Values are within bounds defined in geoninja_backend.core.param_registry.
    return {
        "year": 2020,
        "thickness": 30.0,
        "wellRadius": 0.2,
        "wellDistance": 100.0,
        "maxDrawdown": 1.5,
        "fluidDensity": 1000.0,
        "fluidSpecHeatCap": 4180.0,
        "porosity": 0.2,
        "hydrCond": 1.0e-5,
        "hydrGrad": 0.01,
        "tempDiff": 5.0,
        "rockDensity": 2050.0,
        "rockSpecHeatCap": 961.0,
        # DD.MM format, combined with year in service.
        "heatPeriodStart": "01.01",
        "heatPeriodEnd": "31.03",
        "coolPeriodStart": "01.04",
        "coolPeriodEnd": "30.06",
    }


def _assert_result_items_match_registry(items: list, registry: dict) -> None:
    by_key = {i.key: i for i in items}

    assert set(by_key.keys()) == set(registry.keys())

    for key, reg in registry.items():
        assert key in by_key
        assert by_key[key].unit == reg.get("unit")

        value = by_key[key].value
        assert value is not None
        assert isinstance(value, int | float | str)

        # For this service we currently expect all values to be numeric.
        assert not isinstance(value, str)
        assert math.isfinite(float(value))


def test_perform_analysis_happy_path_returns_all_keys_and_units() -> None:
    results = analysis_service.perform_analysis(_valid_params())

    assert results.status == "ok"
    assert results.message is None
    assert results.derived_quantities is not None
    assert results.ates_kpi_results is not None

    _assert_result_items_match_registry(results.derived_quantities, DERIVED_QUANTITY_REGISTRY)
    _assert_result_items_match_registry(results.ates_kpi_results, ATES_KPI_RESULT_REGISTRY)


def test_perform_analysis_missing_param_returns_validation_error() -> None:
    params = _valid_params()
    params.pop("thickness")

    results = analysis_service.perform_analysis(params)

    assert results.status == "error"
    assert results.derived_quantities is None
    assert results.ates_kpi_results is None
    assert results.message is not None
    assert "Missing required parameter 'thickness'" in results.message


def test_perform_analysis_invalid_date_format_returns_validation_error() -> None:
    params = _valid_params()
    params["heatPeriodStart"] = "1/2"

    results = analysis_service.perform_analysis(params)

    assert results.status == "error"
    assert results.derived_quantities is None
    assert results.ates_kpi_results is None
    assert results.message is not None
    assert "heatPeriodStart" in results.message
    assert "DD.MM" in results.message


def test_perform_analysis_unexpected_exception_returns_generic_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_: dict[str, float | str]) -> analysis_service.AnalysisInputs:  # type: ignore[name-defined]
        raise RuntimeError("kaboom")

    monkeypatch.setattr(analysis_service, "_build_analysis_inputs", boom)

    results = analysis_service.perform_analysis(_valid_params())

    assert results.status == "error"
    assert results.message == "ATES KPI computation failed"
    assert results.derived_quantities is None
    assert results.ates_kpi_results is None
