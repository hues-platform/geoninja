import math

from fastapi.testclient import TestClient

from geoninja_backend.core.analysis_result_registry import (
    ATES_KPI_RESULT_REGISTRY,
    DERIVED_QUANTITY_REGISTRY,
)
from geoninja_backend.main import app


def _valid_params() -> dict[str, float | str]:
    # Keep this aligned with bounds in geoninja_backend.core.param_registry.
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
        "heatPeriodStart": "01.01",
        "heatPeriodEnd": "31.03",
        "coolPeriodStart": "01.04",
        "coolPeriodEnd": "30.06",
    }


def test_run_analysis_happy_path_echoes_location_and_runid_and_returns_results() -> None:
    client = TestClient(app)

    payload = {
        "location": {"lat": 47.4, "lng": 8.5},
        "params": _valid_params(),
        "runId": 123,
    }

    r = client.post("/api/analysis/run", json=payload)
    assert r.status_code == 200

    data = r.json()

    assert data["location"] == payload["location"]
    assert data["runId"] == 123

    results = data["results"]
    assert results["status"] == "ok"
    assert results["message"] is None

    derived = results["derived_quantities"]
    kpis = results["ates_kpi_results"]
    assert isinstance(derived, list)
    assert isinstance(kpis, list)

    derived_by_key = {i["key"]: i for i in derived}
    kpis_by_key = {i["key"]: i for i in kpis}

    assert set(derived_by_key.keys()) == set(DERIVED_QUANTITY_REGISTRY.keys())
    assert set(kpis_by_key.keys()) == set(ATES_KPI_RESULT_REGISTRY.keys())

    for key, reg in DERIVED_QUANTITY_REGISTRY.items():
        item = derived_by_key[key]
        assert item["unit"] == reg["unit"]
        assert item["value"] is not None
        assert math.isfinite(float(item["value"]))

    for key, reg in ATES_KPI_RESULT_REGISTRY.items():
        item = kpis_by_key[key]
        assert item["unit"] == reg["unit"]
        assert item["value"] is not None
        assert math.isfinite(float(item["value"]))


def test_run_analysis_validation_error_returns_error_results_payload() -> None:
    client = TestClient(app)

    params = _valid_params()
    params.pop("thickness")

    payload = {
        "location": {"lat": 47.4, "lng": 8.5},
        "params": params,
    }

    r = client.post("/api/analysis/run", json=payload)
    assert r.status_code == 200

    data = r.json()
    results = data["results"]

    assert results["status"] == "error"
    assert results["derived_quantities"] is None
    assert results["ates_kpi_results"] is None
    assert "Missing required parameter 'thickness'" in results["message"]


def test_run_analysis_request_model_validation_missing_location_is_422() -> None:
    client = TestClient(app)

    payload = {
        "params": _valid_params(),
    }

    r = client.post("/api/analysis/run", json=payload)
    assert r.status_code == 422
