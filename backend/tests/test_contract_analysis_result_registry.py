from __future__ import annotations

import json
from pathlib import Path

from geoninja_backend.core.analysis_result_registry import (
    ATES_KPI_RESULT_REGISTRY,
    DERIVED_QUANTITY_REGISTRY,
)


def load_contract() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    contract_path = repo_root / "contracts" / "analysis_results.json"
    with contract_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_contract_entry(e: dict) -> dict:
    return {
        "key": e.get("key"),
        "unit": e.get("unit", None),
    }


def normalize_registry_entry(key: str, e: dict) -> dict:
    return {"key": key, "unit": e.get("unit", None)}


def test_backend_registry_matches_contract_for_supported_keys():
    contract = load_contract()

    # Derived quantities
    contract_derived = contract["derived_quantities"]
    contract_derived_by_key = {p["key"]: normalize_contract_entry(p) for p in contract_derived}

    for key, reg_entry in DERIVED_QUANTITY_REGISTRY.items():
        assert key in contract_derived_by_key, f"Backend registry key not found in contract: {key}"
        assert (
            normalize_registry_entry(key, reg_entry) == contract_derived_by_key[key]
        ), f"Backend registry entry does not match contract for key: {key}"

    # KPI results
    contract_kpis = contract["ates_kpi_results"]
    contract_kpis_by_key = {p["key"]: normalize_contract_entry(p) for p in contract_kpis}

    for key, reg_entry in ATES_KPI_RESULT_REGISTRY.items():
        assert key in contract_kpis_by_key, f"Backend registry key not found in contract: {key}"
        assert (
            normalize_registry_entry(key, reg_entry) == contract_kpis_by_key[key]
        ), f"Backend registry entry does not match contract for key: {key}"


def test_backend_registry_contains_all_params_from_contract():
    contract = load_contract()

    contract_derived_keys = sorted(p["key"] for p in contract["derived_quantities"])
    backend_derived_keys = sorted(DERIVED_QUANTITY_REGISTRY.keys())

    assert backend_derived_keys == contract_derived_keys, (
        "Backend registry does not include all derived quantities from contract.\n"
        f"Missing from backend: {set(contract_derived_keys) - set(backend_derived_keys)}\n"
        f"Extra in backend: {set(backend_derived_keys) - set(contract_derived_keys)}"
    )

    contract_kpi_keys = sorted(p["key"] for p in contract["ates_kpi_results"])
    backend_kpi_keys = sorted(ATES_KPI_RESULT_REGISTRY.keys())

    assert backend_kpi_keys == contract_kpi_keys, (
        "Backend registry does not include all KPI results from contract.\n"
        f"Missing from backend: {set(contract_kpi_keys) - set(backend_kpi_keys)}\n"
        f"Extra in backend: {set(backend_kpi_keys) - set(contract_kpi_keys)}"
    )
