# Use Python 3.10 slim image
FROM python:3.10-slim

WORKDIR /app

# Install only required system dependencies (minimal footprint)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (layer caching: only re-run if this file changes)
COPY requirements-production.txt .
RUN pip install --no-cache-dir --quiet -r requirements-production.txt

# Pre-download EasyOCR English model in separate layer
# This caches the model download independently
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False, verbose=False)" && \
    echo "✓ EasyOCR English model cached (faster first request)"

# Copy application code (layer caching: cached dependencies stay if only app code changes)
COPY app/ app/

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]