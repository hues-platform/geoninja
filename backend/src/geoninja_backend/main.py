"""FastAPI application entrypoint.

This module constructs the GeoNinja backend FastAPI app and wires together:

- API routing (see :mod:`geoninja_backend.api.router`)
- Application startup lifecycle (preloading lookup datasets)
- App metadata (title/version) used for the OpenAPI contract

OpenAPI contract
---------------
FastAPI exposes the OpenAPI schema at ``/openapi.json``.

This repository additionally commits a snapshot of that schema to
``contracts/openapi.json`` so the frontend can generate stable TypeScript types
without needing a running backend. A backend test asserts the live schema matches
the committed snapshot.

Startup behavior
----------------
On startup the app preloads the datasets used by the local-parameter lookup
endpoints (GLiM, GLHYMPS, and the hydraulic gradient raster). This keeps request
latency predictable but requires the corresponding data artifacts to be present
under ``backend/data`` (typically produced by the data pipeline).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from geoninja_backend import __version__
from geoninja_backend.api.router import api_router
from geoninja_backend.services.glhymps_lookup import load_glhymps_gdf
from geoninja_backend.services.glim_lookup import load_glim_gdf
from geoninja_backend.services.hydr_grad_lookup import load_hydr_grad_raster

logging.basicConfig(
    level=logging.INFO,
    format="INFO:     %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan hook.

    Preloads lookup datasets at application startup.

    Note:
        The ``app`` argument is provided by FastAPI. It is not currently used,
        but kept in the signature to match the expected lifespan protocol.
    """
    load_glim_gdf()
    load_glhymps_gdf()
    load_hydr_grad_raster()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="GeoNinja Backend",
        version=__version__,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
