"""Top-level API router.

This module composes the application's route groups into a single `APIRouter`
instance that is mounted by the FastAPI app (see :mod:`geoninja_backend.main`).

All routers are currently mounted under the same `/api` prefix, so individual
route modules define paths relative to that prefix.

Changing prefixes or included routers will change the public HTTP API surface
and therefore the generated OpenAPI schema (`/openapi.json`) and the committed
snapshot in `contracts/openapi.json`.
"""

from fastapi import APIRouter

from geoninja_backend.api.analysis_routes import router as analysis_router
from geoninja_backend.api.local_param_routes import router as local_params_router

api_router = APIRouter()
api_router.include_router(local_params_router, prefix="/api")
api_router.include_router(analysis_router, prefix="/api")
