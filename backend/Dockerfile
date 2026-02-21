# Use Python 3.10 slim image
FROM python:3.10-slim

# CRITICAL: Install Tesseract BEFORE anything else to avoid caching issues
# This must happen in the base layer, not a cached one
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
        tesseract-ocr \
        libtesseract0 \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* && \
    echo "Tesseract installation status:" && \
    ls -la /usr/bin/tesseract && \
    /usr/bin/tesseract --version

# Fail build immediately if Tesseract is missing
RUN test -x /usr/bin/tesseract || { echo "CRITICAL ERROR: Tesseract not found!"; exit 1; }

WORKDIR /app

# Copy and install Python dependencies
COPY requirements-production.txt .
RUN pip install --no-cache-dir -r requirements-production.txt

# Copy app code
COPY . .

# Set Tesseract environment
ENV TESSERACT_PATH=/usr/bin/tesseract \
    PATH="/usr/bin:$PATH"

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]