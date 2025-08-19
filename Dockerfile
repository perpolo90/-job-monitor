# Use Python 3.11 slim image for smaller size and reliability
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Europe/Warsaw
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port for health check
EXPOSE 8000

# Health check - more lenient for startup
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)" || exit 1

# Default command
CMD ["python", "startup.py"]
