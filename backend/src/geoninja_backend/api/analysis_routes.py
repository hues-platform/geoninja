"""Analysis execution routes.

This module exposes the HTTP endpoints used by the frontend to run the backend
analysis given a set of input parameters.

Contract note
-------------
The analysis request/response schemas are part of the backend OpenAPI spec
(`/openapi.json`) which is snapshotted to `contracts/openapi.json`.

Additionally, the *set of result keys and units* produced by the analysis is
tracked in `contracts/analysis_results.json` and mirrored in backend/frontend
registries and UI metadata.
"""

from fastapi import APIRouter

from geoninja_backend.models.analysis_run import AnalysisRunRequest, AnalysisRunResponse
from geoninja_backend.services.analysis import perform_analysis

router = APIRouter(tags=["Analysis"])


@router.post("/analysis/run", response_model=AnalysisRunResponse)
def run_analysis(req: AnalysisRunRequest) -> AnalysisRunResponse:
    """Run an analysis for the given parameters.

    Args:
        req: Request model containing `location` (lat/lng) and a `params` object
            whose keys correspond to the parameter registry.

    Returns:
        An :class:`~geoninja_backend.models.analysis_run.AnalysisRunResponse`
        containing the provided location, a `results` object (status + result
        lists), and an optional `runId`.
    """
    results = perform_analysis(req.params)
    return AnalysisRunResponse(
        location=req.location,
        results=results,
        runId=req.runId,
    )
