# Use Python 3.10 slim image
FROM python:3.10-slim

# Install all system dependencies for Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract0 \
    libleptonica-dev \
    tesseract-ocr-eng \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Verify tesseract installation and show path
RUN which tesseract \
    && tesseract --version \
    && echo "Tesseract binary location:" \
    && which tesseract

# Copy requirements first
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Set environment variable for Tesseract
ENV TESSERACT_PATH=/usr/bin/tesseract

# Expose Render port
EXPOSE 10000

# Use dynamic port from Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]