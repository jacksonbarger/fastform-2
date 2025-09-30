FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source code and requirements
COPY pyproject.toml ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install dependencies
RUN python -m pip install --upgrade pip && \
    python -m pip install -e .

# Create database during build
RUN python scripts/ingest_formulary.py && \
    python scripts/migrate_to_multi_formulary.py

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8000

# Expose port
EXPOSE 8000

# Note: Railway handles healthchecks, no Docker HEALTHCHECK needed

# Run the application
WORKDIR /app/src
CMD ["sh", "-c", "python -m uvicorn fastform.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
