FROM python:3.13-slim

WORKDIR /app

# System deps:
# - build-essential: compilation toolchain (often needed)
# - gdal/proj/geos: rasterio runtime dependencies (and sometimes build deps if no wheel matches)
# - ca-certificates: TLS
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    gdal-bin \
    libgdal-dev \
    proj-bin \
    libproj-dev \
    libgeos-dev \
  && rm -rf /var/lib/apt/lists/*

# Helpful for builds that need to find gdal-config
ENV GDAL_CONFIG=/usr/bin/gdal-config

RUN pip install --no-cache-dir poetry

WORKDIR /app/backend

# Copy dependency manifests first (cache-friendly)
COPY backend/pyproject.toml backend/poetry.lock* ./
COPY backend/README.md ./README.md

# Copy the actual package sources needed for installing "the current project"
COPY backend/src ./src

# Install deps + install the project package
RUN poetry config virtualenvs.create false \
  && poetry install --without dev --no-interaction --no-ansi

# Copy the rest of the backend (configs, etc.)
COPY backend/ ./

# Shared contracts
COPY contracts/ /app/contracts/

EXPOSE 8000
CMD ["uvicorn", "geoninja_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
