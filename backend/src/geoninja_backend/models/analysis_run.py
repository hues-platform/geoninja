"""Pydantic models for analysis execution.

These models define the request/response payloads for the analysis endpoint
(`POST /api/analysis/run`). They are part of the backend's public API surface and
therefore appear in the generated OpenAPI schema (`/openapi.json`).

Key/Unit contracts
------------------
The `key` values used in :class:`AnalysisResultItem` are not arbitrary: they are
tracked in the shared contract at `contracts/analysis_results.json` and mirrored
in backend registries and frontend UI metadata.

The analysis endpoint may return `null` result lists when a computation is not
available or fails; clients should rely on the `status` and `message` fields to
determine whether results are usable.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from geoninja_backend.models.common import LatLng


class AnalysisRunRequest(BaseModel):
    """Request model for an analysis run.

    Attributes:
        location: Lat/lng for contextual lookups (and for echoing in responses).
        params: Input parameters for the analysis. Keys correspond to the shared
            parameter registry.
        runId: Optional client-provided run identifier.
        startedAt: Optional client timestamp (epoch seconds or ms depending on
            client convention).
        optInputs: Optional extra inputs that may be `null` per key.
    """

    location: LatLng
    params: dict[str, float | str]
    runId: int | None = None
    startedAt: int | None = None
    optInputs: dict[str, float | str | None] | None = None

    model_config = ConfigDict(extra="forbid")


class AnalysisRunResponse(BaseModel):
    """Response model for an analysis run."""

    location: LatLng
    results: AnalysisRunResults
    runId: int | None = None

    model_config = ConfigDict(extra="forbid")


class AnalysisRunResults(BaseModel):
    """Results model for an analysis run.

    Attributes:
        ates_kpi_results: List of KPI-type results (may be `null`).
        derived_quantities: List of derived-quantity results (may be `null`).
        status: Overall status of the computation.
        message: Optional human-readable context (typically present on errors).
    """

    ates_kpi_results: list[AnalysisResultItem] | None = None
    derived_quantities: list[AnalysisResultItem] | None = None
    status: AnalysisResultStatus
    message: str | None = None

    model_config = ConfigDict(extra="forbid")


# Possible statuses for analysis results.
AnalysisResultStatus = Literal["ok", "error"]


class AnalysisResultItem(BaseModel):
    """A single analysis result item.

    Attributes:
        key: Stable identifier for this result.
        value: Numeric or string value (may be `null`).
        unit: Unit string (may be `null`), expected to match the contract.
    """

    key: str
    value: float | str | None = None
    unit: str | None = None

    model_config = ConfigDict(extra="forbid")
