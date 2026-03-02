"""Local parameter lookup routes.

These routes provide *location-dependent* parameter values used as inputs to
analysis runs.

The frontend submits a list of parameter keys and a lat/lng location; the backend
responds with per-key results indicating:

- `ok`: a value was resolved
- `missing`: the key is supported, but no value could be determined for the given location
- `unsupported`: the key is not supported by this endpoint
- `error`: the key is supported, but an exception occurred while resolving it

Data sources
------------
This endpoint combines multiple local data sources:

- GLiM (raster data): lithology classification used for `rockType` and as an
    index into the rock-properties table.
- Rock properties (CSV lookup): maps GLiM lithology keys to representative
    `rockDensity`, `rockSpecHeatCap`, and `rockThermCond`.
- GLHYMPS (vector polygons): used for `hydrCond` lookup.
- Hydraulic gradient (raster data): used for `hydrGrad` lookup.

Contract note
-------------
Parameter keys and metadata are defined centrally in the shared contract
(`contracts/params.json`) and mirrored in backend/frontend registries.
"""

from fastapi import APIRouter

from geoninja_backend.core.param_registry import PARAM_REGISTRY
from geoninja_backend.models.local_param_lookup import (
    ParamLookupRequest,
    ParamLookupResponse,
    ParamLookupResultItem,
)
from geoninja_backend.services.glhymps_lookup import GlhympsLookupResult, lookup_glhymps_at
from geoninja_backend.services.glim_lookup import GlimLithoKey, lookup_glim_at
from geoninja_backend.services.hydr_grad_lookup import HydrGradLookupResult, lookup_hydr_grad_at
from geoninja_backend.services.param_access import is_param_key
from geoninja_backend.services.period_seg import PeriodSegmentationResult, perform_period_seg
from geoninja_backend.services.rock_properties import get_rock_properties

router = APIRouter(tags=["Local Parameters"])

# Keys that require GLiM lookup
_GLIM_DEPENDENT_KEYS = {"rockType", "rockDensity", "rockSpecHeatCap", "rockThermCond"}
_GLHYMPS_DEPENDENT_KEYS = {"hydrCond"}
_HYDRGRAD_DEPENDENT_KEYS = {"hydrGrad"}

# Map API key -> RockProperties attribute name
_ROCK_PROP_ATTR = {
    "rockDensity": "density",
    "rockSpecHeatCap": "spec_heat_cap",
    "rockThermCond": "therm_cond",
}

# Map API key -> Period segmenation attribute key
_PERIOD_SEG_ATTR = {
    "heatPeriodStart": "heat_period_start",
    "heatPeriodEnd": "heat_period_end",
    "coolPeriodStart": "cool_period_start",
    "coolPeriodEnd": "cool_period_end",
}

# Map GlimLithoKey to human-readable label
RockLabelByGlimLithoKey: dict[GlimLithoKey, str] = {
    GlimLithoKey.EVAPORITES: "Evaporites",
    GlimLithoKey.METAMORPHITES: "Metamorphites",
    GlimLithoKey.ACID_PLUTONIC_ROCKS: "Acid Plutonic Rocks",
    GlimLithoKey.BASIC_PLUTONIC_ROCKS: "Basic Plutonic Rocks",
    GlimLithoKey.INTERMEDIATE_PLUTONIC_ROCKS: "Intermediate Plutonic Rocks",
    GlimLithoKey.PYROCLASTICS: "Pyroclastics",
    GlimLithoKey.CARBONATE_SEDIMENTARY_ROCKS: "Carbonate Sedimentary Rocks",
    GlimLithoKey.MIXED_SEDIMENTARY_ROCKS: "Mixed Sedimentary Rocks",
    GlimLithoKey.SILICICLASTIC_SEDIMENTARY_ROCKS: "Siliciclastic Sedimentary Rocks",
    GlimLithoKey.UNCONSOLIDATED_SEDIMENTS: "Unconsolidated Sediments",
    GlimLithoKey.ACID_VOLCANIC_ROCKS: "Acid Volcanic Rocks",
    GlimLithoKey.BASIC_VOLCANIC_ROCKS: "Basic Volcanic Rocks",
    GlimLithoKey.INTERMEDIATE_VOLCANIC_ROCKS: "Intermediate Volcanic Rocks",
    GlimLithoKey.WATER_BODIES: "Water Bodies",
    GlimLithoKey.ICE_AND_GLACIERS: "Ice and Glaciers",
    GlimLithoKey.NO_DATA: "No Data",
}


@router.post("/local_params/lookup", response_model=ParamLookupResponse)
def lookup_local_params(req: ParamLookupRequest) -> ParamLookupResponse:
    """Resolve local parameters for a given location.

    Request:
        - `location`: latitude/longitude
        - `keys`: list of parameter keys to resolve

    Response:
        Returns one :class:`~geoninja_backend.models.local_param_lookup.ParamLookupResultItem`
        per requested key. Keys are processed independently; a missing value for one
        key does not prevent other keys from resolving.

    Implementation notes:
        - Expensive lookups (GLiM/GLHYMPS/raster sampling) are performed at most once
          per request when any requested key depends on that dataset.
        - Some keys are currently hard-coded (e.g., heating/cooling period boundaries).
    """
    results: list[ParamLookupResultItem] = []

    lat = req.location.lat
    lng = req.location.lng

    # Preload GLiM lookup and rock properties if needed
    glim_litho_key: GlimLithoKey | None = None
    if any(key in _GLIM_DEPENDENT_KEYS for key in req.keys):
        glim_lookup_res = lookup_glim_at(lat, lng)
        glim_litho_key = glim_lookup_res.litho_key
    rock_props = None
    if glim_litho_key is not None and any(k in _ROCK_PROP_ATTR for k in req.keys):
        try:
            rock_props = get_rock_properties(glim_litho_key)
        except KeyError:
            rock_props = None  # e.g., wb/ig/nd not defined → treat as missing

    # Preload GLHYMPS lookup if needed
    glhymps_lookup_res: GlhympsLookupResult = GlhympsLookupResult(None, False)
    if any(key in _GLHYMPS_DEPENDENT_KEYS for key in req.keys):
        glhymps_lookup_res = lookup_glhymps_at(lat, lng)

    # Preload hydr_grad lookup if needed
    hydr_grad_lookup_res: HydrGradLookupResult = HydrGradLookupResult(None, False)
    if any(key in _HYDRGRAD_DEPENDENT_KEYS for key in req.keys):
        hydr_grad_lookup_res = lookup_hydr_grad_at(lat, lng)

    # Preload period segmentation if needed
    period_res: PeriodSegmentationResult = PeriodSegmentationResult(None, None, None, None, False)
    period_err: str | None = None
    if any(key in _PERIOD_SEG_ATTR for key in req.keys):
        year = _get_year_input(req)
        if year is None:
            period_err = "Missing or invalid 'year' input for period segmentation"
        else:
            period_res = perform_period_seg(lat, lng, year)

    for key in req.keys:
        # Get param definition; handle unsupported keys
        if not is_param_key(key):
            results.append(ParamLookupResultItem(key=key, status="unsupported", value=None))
            continue
        pdef = PARAM_REGISTRY[key]

        # GLiM-backed rockType
        if key == "rockType":
            results.append(
                ParamLookupResultItem(
                    key=key,
                    status="ok" if glim_litho_key is not None else "missing",
                    value=RockLabelByGlimLithoKey.get(glim_litho_key, None) if glim_litho_key is not None else None,
                )
            )
            continue

        # Derived rock properties
        if key in _ROCK_PROP_ATTR:
            attr = _ROCK_PROP_ATTR[key]
            value = getattr(rock_props, attr) if rock_props is not None else None
            results.append(
                ParamLookupResultItem(
                    key=key,
                    status="ok" if rock_props is not None else "missing",
                    value=value,
                )
            )
            continue

        # Hydraulic conductivity
        if key == "hydrCond":
            results.append(
                ParamLookupResultItem(
                    key=key,
                    status="ok" if glhymps_lookup_res.hydr_cond is not None else "missing",
                    value=glhymps_lookup_res.hydr_cond,
                )
            )
            continue

        if key == "hydrGrad":
            results.append(
                ParamLookupResultItem(
                    key=key,
                    status="ok" if hydr_grad_lookup_res.hydr_grad is not None else "missing",
                    value=hydr_grad_lookup_res.hydr_grad,
                )
            )
            continue

        # Period segmenation
        if key in _PERIOD_SEG_ATTR:
            if period_err is not None:
                results.append(
                    ParamLookupResultItem(
                        key=key,
                        status="error",
                        value=None,
                        message=period_err,
                    )
                )
                continue

            attr = _PERIOD_SEG_ATTR[key]
            value = getattr(period_res, attr)
            results.append(
                ParamLookupResultItem(
                    key=key,
                    status="ok" if value is not None else "missing",
                    value=value,
                )
            )
            continue

        # Placeholder for other supported params (for now)
        if pdef["valueType"] == "number":
            results.append(ParamLookupResultItem(key=key, status="unsupported", value=0.0))
        else:
            results.append(ParamLookupResultItem(key=key, status="unsupported", value=""))

    return ParamLookupResponse(location=req.location, results=results)


def _get_year_input(req: ParamLookupRequest) -> int | None:
    if req.inputs is None:
        return None
    v = req.inputs.get("year")
    return v if isinstance(v, int) else None
