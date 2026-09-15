FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (git, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root forge user
RUN groupadd -r forge && useradd -r -g forge -d /app -s /sbin/nologin forge

# Copy project files
COPY . /app

# Install python dependencies and forge packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
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
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
