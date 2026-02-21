# Use Python 3.10 slim image - based on Debian 12
FROM python:3.10-slim

# Force fresh build (cache bust) - update this when needing fresh build
ARG BUILD_DATE=2026-02-22
ENV BUILD_DATE=$BUILD_DATE

# Update package lists and install Tesseract + dependencies
# Using explicit install with verbose output for debugging
RUN echo "=== Installing Tesseract OCR ===" && \
    apt-get update --allow-unauthenticated && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract0 \
    tesseract-ocr-eng \
    && echo "=== Tesseract installation complete ===" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Fail the build if Tesseract is not found
RUN echo "=== CRITICAL: Verifying Tesseract ===" && \
    test -f /usr/bin/tesseract || (echo "ERROR: /usr/bin/tesseract not found!" && exit 1) && \
    /usr/bin/tesseract --version && \
    echo "✓ Tesseract verified successfully"

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Set environment variables for Tesseract
ENV TESSERACT_PATH=/usr/bin/tesseract \
    PATH="/usr/bin:$PATH" \
    LD_LIBRARY_PATH="/usr/lib:$LD_LIBRARY_PATH"

# Expose Render port
EXPOSE 10000

# Run the app
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]