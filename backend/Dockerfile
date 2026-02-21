# Use Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Tesseract OCR with multiple approaches for reliability
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract0 \
    tesseract-ocr-eng \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation - fail build if not found
RUN echo "Checking Tesseract installation..." && \
    which tesseract && \
    tesseract --version && \
    ls -la $(which tesseract) || (echo "ERROR: Tesseract not found!" && exit 1)

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Set environment for Tesseract
ENV TESSERACT_PATH=/usr/bin/tesseract

# Expose Render port
EXPOSE 10000

# Use dynamic port from Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]