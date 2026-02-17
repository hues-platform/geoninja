# GeoNinja Frontend

React + TypeScript frontend (Vite) for GeoNinja.

The frontend is designed to work against the FastAPI backend in `../backend` and
uses generated TypeScript types from the committed OpenAPI snapshot in
`../contracts/openapi.json`.

## Prerequisites

- Node.js + npm

## Setup

From the repo root:

```bash
cd frontend
npm install
```

## Run (development)

Start the backend first (defaults to `http://127.0.0.1:8000`). Then run:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite (typically `http://localhost:5173`).

### API routing in dev

In development, the frontend calls the backend via a Vite proxy:

- Frontend requests use the path prefix `/api/...`
- Vite forwards `/api` to `http://localhost:8000`

This proxy is configured in `frontend/vite.config.ts`.

## Quality checks

All commands below are run from `frontend/`.

- Lint:

```bash
npm run lint
```

- Typecheck:

```bash
npm run typecheck
```

- Tests (Vitest):

```bash
npm run test
```

- Format:

```bash
npm run format
```

## Build + preview

```bash
npm run build
npm run preview
```

## OpenAPI contract and generated types

The frontend consumes OpenAPI-derived types generated into:

- `src/api/_generated/openapi.types.ts`

Generation uses `openapi-typescript` against the committed contract snapshot:

- `../contracts/openapi.json`

To regenerate types:

```bash
cd frontend
npx openapi-typescript ../contracts/openapi.json -o src/api/_generated/openapi.types.ts
```

If you update backend routes/schemas, rebase the OpenAPI contract first (see
`backend/scripts/rebase_openapi_contract.py`), then regenerate frontend types.

In VS Code, you can use the workspace task:

- “API: rebase contract & regenerate frontend types”

## Project layout (high level)

- `src/api/`: API client functions and error helpers
- `src/process/`: app workflows (marker → param lookup → analysis run)
- `src/components/`: UI components (control panel, results, popups)
- `src/map/`: Leaflet map integration and base layers
- `src/config/`: contract-backed parameter/result metadata + validation helpers
- `src/types/`: shared domain types

## Docker

The repo includes a `frontend/Dockerfile` and root-level `docker-compose.yaml`.
If you use Docker for local dev, start it from the repo root:

```bash
docker compose up --build
```
