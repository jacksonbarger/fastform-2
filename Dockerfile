FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy source code
COPY src/ ./src/
COPY fastform.db ./fastform.db

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/v1/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "fastform.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
