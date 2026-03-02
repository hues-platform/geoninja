FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    libexpat1 \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

# Work in the data_pipeline project root
WORKDIR /repo/data_pipeline

# Copy dependency manifests (cache-friendly)
COPY data_pipeline/pyproject.toml data_pipeline/poetry.lock* ./

# Copy source
COPY data_pipeline/src ./src

# Install into global env (no venv)
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
