# backend/Dockerfile
# Production-ready FastAPI application
# Uses Python 3.13 for latest performance and security features

FROM python:3.11-slim as production

WORKDIR /app

# Install system dependencies including build tools
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory for mounted geolocation data
RUN mkdir -p ./data/geolocation

# Copy application code
COPY app/ ./app/

# Expose port for Cloud Run compatibility
EXPOSE 8080

# Default command - use PORT environment variable for Cloud Run compatibility
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]