# GeoNinja Contracts

This directory contains **formal interface contracts** between the GeoNinja backend and frontend. These files define *what* data is exchanged and *how it is structured*, independent of implementation details.

The contracts serve three main purposes:

1. **Stability** – they define a stable API and data model boundary
2. **Coordination** – they align backend, frontend, and analysis logic
3. **Verification** – they can be versioned, snapshotted, and tested

No application logic should live in this directory.

---

## Contents

### `params.json`

**Parameter registry contract**

This file defines the complete set of input parameters understood by GeoNinja. It is the single source of truth for:

- Which parameters exist
- Whether they are *static* (user-defined) or *local* (location-dependent)
- Data types, units, and valid ranges
- Default values (if applicable)

Typical consumers:
- Frontend parameter forms and validation
- Backend parameter validation and normalization
- Analysis input preparation

Each parameter entry includes:

- `key`: canonical identifier used across the system
- `paramType`: `static` or `local`
- `valueType`: `number` or `string`
- `unit`: physical unit (or `null`)
- `min` / `max`: admissible value range (if numeric)
- `default`: optional default value

This file should only change when the *semantic input space* of GeoNinja changes.

---

### `analysis_results.json`

**Analysis output contract**

This file defines the *expected structure* of analysis results produced by the backend. It is split into two conceptual groups:

#### 1. `derived_quantities`

Intermediate physical quantities derived from inputs and location data, such as:

- Hydraulic transmissivity
- Darcy and pore velocities
- Volumetric heat capacities
- Storativity
- Heating / cooling period lengths

These quantities are typically useful for:
- Debugging
- Scientific inspection
- Advanced users

#### 2. `ates_kpi_results`

High-level ATES performance indicators, such as:

- Maximum volumetric and mass flow rates
- Maximum heating / cooling power
- Thermal radii and affected areas
- Areal heat and cooling densities

Each result entry defines:

- `key`: canonical identifier
- `unit`: physical unit of the result

The *numerical computation* of these quantities is out of scope here; this file only defines **what results exist and how they are named**.

---

### `openapi.json`

**Backend HTTP API contract (OpenAPI 3.1)**

This is a snapshot of the GeoNinja backend's public API, generated from FastAPI. It defines:

- Available endpoints
- Request and response schemas
- Validation rules
- Error formats

Key endpoints include:

- `POST /api/local_params/lookup`
- `POST /api/analysis/run`

This file is primarily used for:

- Frontend–backend integration
- Automated contract tests (snapshot testing)
- External client generation or inspection

It should be updated **only when the backend API changes intentionally**.

---

## Versioning and workflow

- Contract files are **version-controlled** and reviewed like code
- Changes should be deliberate and minimal
- Breaking changes must be coordinated across backend and frontend

Typical workflow:

1. Change backend logic or data model
2. Update the corresponding contract file
3. Update frontend / consumers
4. Update snapshot or integration tests

---

## Design philosophy

- Contracts describe **interfaces, not implementations**
- They are **technology-agnostic** (JSON, OpenAPI)
- They favor **explicitness over convenience**

If something appears redundant here, that is usually intentional.
