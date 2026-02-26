FROM python:3.13-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry

# We mount the repo at /repo in docker-compose
WORKDIR /repo/data_pipeline

# Copy dependency manifests (cache-friendly)
WORKDIR /repo/data_pipeline
COPY data_pipeline/pyproject.toml data_pipeline/poetry.lock* ./

# Copy the package source so Poetry can install the current project
COPY data_pipeline/src ./src

# Install backend deps into global env (no venv)
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
