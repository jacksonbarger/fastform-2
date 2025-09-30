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
RUN python scripts/ingest_formulary.py

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run the application
WORKDIR /app/src
CMD ["python", "-m", "uvicorn", "fastform.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
