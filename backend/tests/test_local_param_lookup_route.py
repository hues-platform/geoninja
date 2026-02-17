from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from geoninja_backend.api import local_param_routes
from geoninja_backend.services.glhymps_lookup import GlhympsLookupResult
from geoninja_backend.services.glim_lookup import (
    GlimLithoKey,
    GlimLookupResult,
)
from geoninja_backend.services.hydr_grad_lookup import HydrGradLookupResult
from geoninja_backend.services.rock_properties import RockProperties


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(local_param_routes.router, prefix="/api")
    return TestClient(app)


def test_lookup_unknown_key_is_unsupported() -> None:
    client = _client()
    payload = {"location": {"lat": 0.0, "lng": 0.0}, "keys": ["doesNotExist"]}

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200

    item = r.json()["results"][0]
    assert item["key"] == "doesNotExist"
    assert item["status"] == "unsupported"
    assert item["value"] is None


def test_lookup_glim_miss_sets_rock_keys_to_missing(monkeypatch) -> None:
    monkeypatch.setattr(local_param_routes, "lookup_glim_at", lambda lat, lng: GlimLookupResult(None, False))

    client = _client()
    payload = {
        "location": {"lat": 1.0, "lng": 2.0},
        "keys": ["rockType", "rockDensity", "rockSpecHeatCap", "rockThermCond"],
    }

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200

    by_key = {i["key"]: i for i in r.json()["results"]}

    assert by_key["rockType"]["status"] == "missing"
    assert by_key["rockType"]["value"] is None

    for k in ["rockDensity", "rockSpecHeatCap", "rockThermCond"]:
        assert by_key[k]["status"] == "missing"
        assert by_key[k]["value"] is None


def test_lookup_rock_props_missing_for_litho_yields_missing_for_props(monkeypatch) -> None:
    monkeypatch.setattr(
        local_param_routes,
        "lookup_glim_at",
        lambda lat, lng: GlimLookupResult(GlimLithoKey.WATER_BODIES, True),
    )

    def raise_keyerror(_: GlimLithoKey):
        raise KeyError("no props")

    monkeypatch.setattr(local_param_routes, "get_rock_properties", raise_keyerror)

    client = _client()
    payload = {
        "location": {"lat": 1.0, "lng": 2.0},
        "keys": ["rockType", "rockDensity", "rockSpecHeatCap", "rockThermCond"],
    }

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200

    by_key = {i["key"]: i for i in r.json()["results"]}

    assert by_key["rockType"]["status"] == "ok"
    assert by_key["rockType"]["value"] == local_param_routes.RockLabelByGlimLithoKey[GlimLithoKey.WATER_BODIES]

    for k in ["rockDensity", "rockSpecHeatCap", "rockThermCond"]:
        assert by_key[k]["status"] == "missing"
        assert by_key[k]["value"] is None


def test_lookup_rock_props_happy_path(monkeypatch) -> None:
    monkeypatch.setattr(
        local_param_routes,
        "lookup_glim_at",
        lambda lat, lng: GlimLookupResult(GlimLithoKey.UNCONSOLIDATED_SEDIMENTS, True),
    )
    monkeypatch.setattr(
        local_param_routes,
        "get_rock_properties",
        lambda litho: RockProperties(density=2000.0, spec_heat_cap=900.0, therm_cond=1.2),
    )

    client = _client()
    payload = {
        "location": {"lat": 1.0, "lng": 2.0},
        "keys": ["rockType", "rockDensity", "rockSpecHeatCap", "rockThermCond"],
    }

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200

    by_key = {i["key"]: i for i in r.json()["results"]}

    assert by_key["rockType"]["status"] == "ok"
    assert by_key["rockDensity"]["status"] == "ok"
    assert by_key["rockDensity"]["value"] == 2000.0
    assert by_key["rockSpecHeatCap"]["status"] == "ok"
    assert by_key["rockSpecHeatCap"]["value"] == 900.0
    assert by_key["rockThermCond"]["status"] == "ok"
    assert by_key["rockThermCond"]["value"] == 1.2


def test_lookup_glhymps_and_hydrgrad_missing(monkeypatch) -> None:
    monkeypatch.setattr(local_param_routes, "lookup_glhymps_at", lambda lat, lng: GlhympsLookupResult(None, False))
    monkeypatch.setattr(local_param_routes, "lookup_hydr_grad_at", lambda lat, lng: HydrGradLookupResult(None, False))

    client = _client()
    payload = {"location": {"lat": 1.0, "lng": 2.0}, "keys": ["hydrCond", "hydrGrad"]}

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200

    by_key = {i["key"]: i for i in r.json()["results"]}

    assert by_key["hydrCond"]["status"] == "missing"
    assert by_key["hydrCond"]["value"] is None

    assert by_key["hydrGrad"]["status"] == "missing"
    assert by_key["hydrGrad"]["value"] is None


def test_lookup_supported_but_unimplemented_numeric_param_is_unsupported_with_placeholder_value() -> None:
    client = _client()

    payload = {
        "location": {"lat": 0.0, "lng": 0.0},
        "keys": ["thickness"],
    }

    r = client.post("/api/local_params/lookup", json=payload)
    assert r.status_code == 200

    item = r.json()["results"][0]
    assert item["key"] == "thickness"
    assert item["status"] == "unsupported"
    assert item["value"] == 0.0
