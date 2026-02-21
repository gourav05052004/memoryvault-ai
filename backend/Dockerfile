# Use Python 3.10 slim image
FROM python:3.10-slim

# Install system dependencies (Tesseract OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Expose Render port
EXPOSE 10000

# Use dynamic port from Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]