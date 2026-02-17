from __future__ import annotations

import json
from pathlib import Path

from geoninja_backend.core.param_registry import PARAM_REGISTRY


def load_contract() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    contract_path = repo_root / "contracts" / "params.json"
    with contract_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_contract_entry(e: dict) -> dict:
    return {
        "key": e.get("key"),
        "paramType": e.get("paramType"),
        "valueType": e.get("valueType"),
        "unit": e.get("unit", None),
        "min": e.get("min", None),
        "max": e.get("max", None),
        "default": e.get("default", None),
    }


def normalize_registry_entry(key, e: dict) -> dict:
    return {
        "key": key,
        "paramType": e.get("paramType"),
        "valueType": e.get("valueType"),
        "unit": e.get("unit", None),
        "min": e.get("min", None),
        "max": e.get("max", None),
        "default": e.get("default", None),
    }


def test_backend_registry_matches_contract_for_supported_keys():
    contract = load_contract()
    contract_params = contract["params"]
    contract_by_key = {p["key"]: normalize_contract_entry(p) for p in contract_params}

    for key, reg_entry in PARAM_REGISTRY.items():
        assert key in contract_by_key, f"Backend registrty key not found in contract: {key}"
        assert (
            normalize_registry_entry(key, reg_entry) == contract_by_key[key]
        ), f"Backend registry entry does not match contract for key: {key}"


def test_backend_registry_contains_all_params_from_contract():
    contract = load_contract()
    contract_local_keys = sorted(p["key"] for p in contract["params"])

    backend_keys = sorted(PARAM_REGISTRY.keys())

    assert backend_keys == contract_local_keys, (
        "Backend registry does not include all local parameters from contract.\n"
        f"Missing from backend: {set(contract_local_keys) - set(backend_keys)}\n"
        f"Extra in backend: {set(backend_keys) - set(contract_local_keys)}"
    )
