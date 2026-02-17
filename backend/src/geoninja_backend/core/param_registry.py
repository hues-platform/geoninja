"""Parameter key and metadata registry.

This module defines the canonical set of parameter keys accepted by the backend
analysis endpoint and/or required for calculations.

Why this exists
---------------
Parameter `key` strings are used across multiple layers:

- backend request parsing and validation
- OpenAPI schema typing (request/response models)
- frontend forms, defaults, and unit display

To avoid drift, the same key set and metadata is also represented in the shared
contract file ``contracts/params.json``. Backend/frontend tests validate that
the contract and in-code registries remain consistent.

Registry shape
--------------
``PARAM_REGISTRY`` maps a ``ParamKey`` to a small metadata record:

- ``paramType``: whether the value is user-provided/static or location-derived
- ``valueType``: the scalar value kind (number/string)
- ``unit``: display unit (or ``None`` for non-numeric)
- ``min``/``max``: optional UI / sanity bounds for numeric values
- ``default``: default scalar value (or ``None`` when not applicable)
"""

from __future__ import annotations

from typing import Literal, TypedDict, TypeGuard

ParamType = Literal["static", "local"]
ValueType = Literal["number", "string"]
Scalar = float | str | None


ParamKey = Literal[
    "year",
    "thickness",
    "wellRadius",
    "wellDistance",
    "maxDrawdown",
    "fluidDensity",
    "fluidSpecHeatCap",
    "porosity",
    "tempDiff",
    "rockType",
    "rockDensity",
    "rockSpecHeatCap",
    "rockThermCond",
    "hydrCond",
    "hydrGrad",
    "heatPeriodStart",
    "heatPeriodEnd",
    "coolPeriodStart",
    "coolPeriodEnd",
]


def is_param_key(key: str) -> TypeGuard[ParamKey]:
    """Return True if a string is a known ``ParamKey``.

    This is primarily used when consuming untyped input (e.g. query params or
    JSON) where we want a type-narrowing guard before indexing
    ``PARAM_REGISTRY``.
    """
    return key in PARAM_REGISTRY


class ParamDef(TypedDict):
    """Metadata describing a parameter key."""

    paramType: ParamType
    valueType: ValueType
    unit: str | None
    min: float | None
    max: float | None
    default: Scalar


PARAM_REGISTRY: dict[ParamKey, ParamDef] = {
    "year": {
        "paramType": "static",
        "valueType": "number",
        "unit": "-",
        "min": 1990,
        "max": 2023,
        "default": 2020,
    },
    "thickness": {
        "paramType": "static",
        "valueType": "number",
        "unit": "m",
        "min": 10,
        "max": 200,
        "default": 30,
    },
    "wellRadius": {
        "paramType": "static",
        "valueType": "number",
        "unit": "m",
        "min": 0.05,
        "max": 2,
        "default": 0.2,
    },
    "wellDistance": {
        "paramType": "static",
        "valueType": "number",
        "unit": "m",
        "min": 10,
        "max": 1000,
        "default": 100,
    },
    "maxDrawdown": {
        "paramType": "static",
        "valueType": "number",
        "unit": "m",
        "min": 1,
        "max": 20,
        "default": 1.5,
    },
    "fluidDensity": {
        "paramType": "static",
        "valueType": "number",
        "unit": "kg/m³",
        "min": 100,
        "max": 2000,
        "default": 1000,
    },
    "fluidSpecHeatCap": {
        "paramType": "static",
        "valueType": "number",
        "unit": "J/(kg·K)",
        "min": 100,
        "max": 10000,
        "default": 4180,
    },
    "porosity": {
        "paramType": "static",
        "valueType": "number",
        "unit": "-",
        "min": 0.01,
        "max": 0.5,
        "default": 0.2,
    },
    "tempDiff": {
        "paramType": "static",
        "valueType": "number",
        "unit": "K",
        "min": 1,
        "max": 20,
        "default": 5,
    },
    "rockType": {
        "paramType": "local",
        "valueType": "string",
        "unit": None,
        "min": None,
        "max": None,
        "default": None,
    },
    "rockDensity": {
        "paramType": "local",
        "valueType": "number",
        "unit": "kg/m³",
        "min": 1000.0,
        "max": 4000.0,
        "default": None,
    },
    "rockSpecHeatCap": {
        "paramType": "local",
        "valueType": "number",
        "unit": "J/(kg·K)",
        "min": 500.0,
        "max": 2000.0,
        "default": None,
    },
    "rockThermCond": {
        "paramType": "local",
        "valueType": "number",
        "unit": "W/(m·K)",
        "min": 0.1,
        "max": 10.0,
        "default": None,
    },
    "hydrCond": {
        "paramType": "local",
        "valueType": "number",
        "unit": "m/s",
        "min": 1e-12,
        "max": 1e-2,
        "default": None,
    },
    "hydrGrad": {
        "paramType": "local",
        "valueType": "number",
        "unit": "-",
        "min": 0,
        "max": 1,
        "default": None,
    },
    "heatPeriodStart": {
        "paramType": "local",
        "valueType": "string",
        "unit": None,
        "min": None,
        "max": None,
        "default": None,
    },
    "heatPeriodEnd": {
        "paramType": "local",
        "valueType": "string",
        "unit": None,
        "min": None,
        "max": None,
        "default": None,
    },
    "coolPeriodStart": {
        "paramType": "local",
        "valueType": "string",
        "unit": None,
        "min": None,
        "max": None,
        "default": None,
    },
    "coolPeriodEnd": {
        "paramType": "local",
        "valueType": "string",
        "unit": None,
        "min": None,
        "max": None,
        "default": None,
    },
}
