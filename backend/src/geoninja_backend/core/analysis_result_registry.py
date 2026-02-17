"""Analysis result key/unit registries.

This module defines the canonical set of analysis result keys produced by the
backend and the unit string associated with each key.

Why this exists
---------------
Result `key` strings are used across multiple layers:

- backend calculation + API serialization
- OpenAPI schema typing (`AnalysisResultItem.key`)
- frontend result rendering/formatting

To keep these layers aligned, the same keys/units are also tracked in the shared
contract file `contracts/analysis_results.json`. Backend tests validate that this
module and that contract file match exactly.

How to extend
-------------
When adding/removing/renaming a result key or changing a unit:

1. Update the appropriate `Literal[...]` key type.
2. Update the corresponding registry mapping.
3. Update `contracts/analysis_results.json`.
4. Update any frontend metadata (labels, ordering, formatting) and run tests.
"""

from typing import Literal, TypedDict

DerivedQuantityKey = Literal[
    "hydrTrans",
    "darcyVelo",
    "poreVelo",
    "thermFrontVelo",
    "retardFact",
    "fluidVolHeatCap",
    "rockVolHeatCap",
    "aqVolHeatCap",
    "heatingDays",
    "coolingDays",
    "maxPumpRate",
    "storativity",
]

AtesKpiResultKey = Literal[
    "maxVolFlowRateHeat",
    "maxVolFlowRateCool",
    "maxMassFlowRateHeat",
    "maxMassFlowRateCool",
    "maxHeatRate",
    "maxCoolRate",
    "thermRadVolEqWarmWell",
    "thermRadVolEqColdWell",
    "thermRadAdvWarmWell",
    "thermRadAdvColdWell",
    "thermRadWarmWell",
    "thermRadColdWell",
    "thermArea",
    "maxHeatDensity",
    "maxCoolDensity",
]


class AnalysisResultDef(TypedDict):
    """Metadata describing a result key."""

    unit: str


DERIVED_QUANTITY_REGISTRY: dict[DerivedQuantityKey, AnalysisResultDef] = {
    "hydrTrans": {
        "unit": "m²/s",
    },
    "darcyVelo": {
        "unit": "m/s",
    },
    "poreVelo": {
        "unit": "m/s",
    },
    "thermFrontVelo": {
        "unit": "m/s",
    },
    "retardFact": {
        "unit": "-",
    },
    "fluidVolHeatCap": {
        "unit": "J/(m³·K)",
    },
    "rockVolHeatCap": {
        "unit": "J/(m³·K)",
    },
    "aqVolHeatCap": {
        "unit": "J/(m³·K)",
    },
    "heatingDays": {
        "unit": "d",
    },
    "coolingDays": {
        "unit": "d",
    },
    "storativity": {
        "unit": "-",
    },
}

ATES_KPI_RESULT_REGISTRY: dict[AtesKpiResultKey, AnalysisResultDef] = {
    "maxVolFlowRateHeat": {
        "unit": "m³/s",
    },
    "maxVolFlowRateCool": {
        "unit": "m³/s",
    },
    "maxMassFlowRateHeat": {
        "unit": "kg/s",
    },
    "maxMassFlowRateCool": {
        "unit": "kg/s",
    },
    "maxHeatRate": {
        "unit": "W",
    },
    "maxCoolRate": {
        "unit": "W",
    },
    "thermRadVolEqWarmWell": {
        "unit": "m",
    },
    "thermRadVolEqColdWell": {
        "unit": "m",
    },
    "thermRadAdvWarmWell": {
        "unit": "m",
    },
    "thermRadAdvColdWell": {
        "unit": "m",
    },
    "thermRadWarmWell": {
        "unit": "m",
    },
    "thermRadColdWell": {
        "unit": "m",
    },
    "thermArea": {
        "unit": "m²",
    },
    "maxHeatDensity": {
        "unit": "W/m²",
    },
    "maxCoolDensity": {
        "unit": "W/m²",
    },
}
