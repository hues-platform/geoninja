"""Pydantic models for local-parameter lookup.

These models define the request/response payloads for the local parameter lookup
endpoint (`POST /api/local_params/lookup`).

The endpoint is designed to resolve multiple keys per request. Each key is
returned with an explicit `status` so clients can distinguish between:

- `ok`: value was resolved
- `missing`: key is supported, but no value exists at the given location
- `unsupported`: key is not supported by the lookup endpoint
- `error`: key is supported, but an exception occurred while resolving it

These models are part of the backend OpenAPI schema (`/openapi.json`) and are
therefore also reflected in the committed snapshot at `contracts/openapi.json`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from geoninja_backend.models.common import LatLng

ParamLookupStatus = Literal["ok", "missing", "unsupported", "error"]
ScalarValue = int | float | str | None


class ParamLookupRequest(BaseModel):
    """Request payload for local parameter lookup.

    Attributes:
        location:
            Latitude/longitude at which to resolve local parameters.

        keys:
            Parameter keys to resolve. Must contain at least one key.

        inputs:
            Optional additional inputs that can influence lookup behaviour.

            Currently, the following global input is supported:

            - ``year`` (int):
                Reference year used for year-dependent lookups such as
                heating/cooling period segmentation (e.g. ``heatPeriodStart``,
                ``coolPeriodEnd``). If any year-dependent keys are requested,
                ``inputs["year"]`` must be provided.
    """

    location: LatLng
    keys: list[str] = Field(min_length=1)
    inputs: dict[str, ScalarValue] | None = None

    model_config = ConfigDict(extra="forbid")


class ParamLookupResultItem(BaseModel):
    """Result for a single requested key."""

    model_config = ConfigDict(extra="forbid")
    key: str
    status: ParamLookupStatus
    value: ScalarValue | None = None
    message: str | None = None


class ParamLookupResponse(BaseModel):
    """Response payload for local parameter lookup."""

    model_config = ConfigDict(extra="forbid")
    location: LatLng
    results: list[ParamLookupResultItem]
