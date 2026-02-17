
# GeoNinja Backend

FastAPI backend for GeoNinja.

It exposes:

- health endpoints (for deploy/runtime checks)
- local parameter lookup endpoints (driven by staged geospatial datasets)
- analysis endpoints (run calculations and returns typed result items)

The backend is intentionally coupled to the shared contract files in the repo
root:

- `contracts/openapi.json` (committed OpenAPI snapshot)
- `contracts/params.json` (parameter registry contract)
- `contracts/analysis_results.json` (analysis-result key/unit contract)

Backend and frontend both run tests to ensure these contracts stay in sync.

## Run locally

From the repo root:

1. Install backend dependencies (use your preferred workflow: venv/conda/uv).
2. Run the API server:

	 - VS Code task: `Backend: run`
	 - Or directly from `backend/`:

		 - `python -m uvicorn geoninja_backend.main:app --host 127.0.0.1 --port 8000`

The API should be available at:

- `http://127.0.0.1:8000/`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Data dependencies (local-parameter lookups)

Some endpoints depend on datasets staged into `backend/data/` by the data
pipeline (at the repo root):

- GLHYMPS (vector polygons)
- GLiM (vector polygons)
- Hydr. gradient (raster)
- Rock properties (CSV lookup table)

If lookups return “no data”, ensure the pipeline has been run at least once:

- VS Code task: `Data pipeline`
- Or: `python -m data_pipeline.run`

## Contracts and OpenAPI workflow

### OpenAPI snapshot

This repo commits a snapshot of the backend OpenAPI document to
`contracts/openapi.json`.

Backend tests assert that the current app OpenAPI output matches the committed
snapshot, to prevent accidental breaking API changes.

To update the snapshot after intentional API changes:

- VS Code task: `Backend: rebase openAPI contract`

### Frontend type generation

The frontend generates TypeScript types from `contracts/openapi.json`.

To update both the OpenAPI snapshot and the frontend-generated types in one go:

- VS Code task: `API: rebase contract & regenerate frontend types`

### Param/result registries

The backend maintains in-code registries that are expected to match the shared
contracts:

- `geoninja_backend.core.param_registry.PARAM_REGISTRY` ↔ `contracts/params.json`
- `geoninja_backend.core.analysis_result_registry.*` ↔ `contracts/analysis_results.json`

If you add/remove keys or change units/defaults, update both sides and run the
test suites.

## Lint and test

From VS Code:

- `Backend: lint` (ruff + mypy)
- `Backend: test` (pytest)

From `backend/` directly:

- Lint:
	- `python -m ruff check src --config pyproject.toml --output-format=full --ignore C901`
	- `python -m mypy src --config-file pyproject.toml`
- Tests:
	- `python -m pytest`

## Project layout

- `src/geoninja_backend/main.py`: FastAPI app factory and lifespan preload
- `src/geoninja_backend/api/`: API routers and endpoints
- `src/geoninja_backend/models/`: Pydantic request/response models
- `src/geoninja_backend/services/`: calculation + data access services
- `src/geoninja_backend/core/`: registries and core shared definitions
- `data/`: staged datasets used for local lookups
