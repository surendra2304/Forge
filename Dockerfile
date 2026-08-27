# Multi-stage Dockerfile for Project FORGE Production Engine

# Stage 1: Build & Dependency Wheel Cache
FROM python:3.11-slim as builder

WORKDIR /install

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip build \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /install/wheels -e . || true

# Stage 2: Final Production Runtime Image
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies (git, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root forge user
RUN groupadd -r forge && useradd -r -g forge -d /app -s /sbin/nologin forge

# Copy project files
COPY . /app

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# Create workspace and data directories with proper permissions
RUN mkdir -p /app/data /app/workspaces /app/artifacts \
    && chown -R forge:forge /app

USER forge

ENV FORGE_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
