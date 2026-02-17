import math

import pytest
from fastapi.testclient import TestClient

from geoninja_backend.main import app

client = TestClient(app)


@pytest.mark.glim
def test_lookup_returns_rocktype_and_rockprops():
    payload = {
        "location": {"lat": 47.4, "lng": 8.5},
        "keys": ["rockType", "rockDensity", "rockSpecHeatCap", "rockThermCond"],
    }
    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200
    data = r.json()

    by_key = {item["key"]: item for item in data["results"]}

    # rockType
    assert by_key["rockType"]["status"] == "ok"
    assert by_key["rockType"]["value"] == "Unconsolidated Sediments"
    # rockDensity
    assert by_key["rockDensity"]["status"] == "ok"
    assert by_key["rockDensity"]["value"] == 2050.0
    # rockSpecHeatCap
    assert by_key["rockSpecHeatCap"]["status"] == "ok"
    assert by_key["rockSpecHeatCap"]["value"] == 961.0
    # rockThermCond
    assert by_key["rockThermCond"]["status"] == "ok"
    assert by_key["rockThermCond"]["value"] == 1.39


@pytest.mark.glhymps
def test_lookup_returns_hydr_cond():
    payload = {
        "location": {"lat": 47.4, "lng": 8.5},
        "keys": ["hydrCond"],
    }
    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200
    data = r.json()

    by_key = {item["key"]: item for item in data["results"]}

    # hydrCond
    assert by_key["hydrCond"]["status"] == "ok"
    assert by_key["hydrCond"]["value"] == pytest.approx(1.1481536214968841e-05)


@pytest.mark.hydr_grad
def test_lookup_returns_hydr_grad():
    payload = {
        "location": {"lat": 50.11, "lng": 8.68},
        "keys": ["hydrGrad"],
    }
    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200
    data = r.json()

    by_key = {item["key"]: item for item in data["results"]}

    assert "hydrGrad" in by_key
    item = by_key["hydrGrad"]

    assert item["status"] == "ok"
    assert item["value"] is not None
    assert isinstance(item["value"], int | float)
    assert math.isfinite(float(item["value"]))
    assert item["value"] >= 0.0


@pytest.mark.glim
def test_lookup_returns_unsupported_for_unknown_keys():
    payload = {
        "location": {"lat": 0, "lng": 0},
        "keys": ["doesNotExist"],
    }

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200
    data = r.json()

    assert len(data["results"]) == 1
    item = data["results"][0]

    assert item["key"] == "doesNotExist"
    assert item["status"] == "unsupported"
    assert item["value"] is None
