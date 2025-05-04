# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV C_FORCE_ROOT 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Optional: Copy celery-ssl.conf for SSL/TLS support (if present)
# COPY docker/celery-ssl.conf ./celery-ssl.conf

# Celery configuration
ENV CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:${REDIS_PORT}/${REDIS_DB}
ENV CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:${REDIS_PORT}/${REDIS_DB}

# Notes:
# - To enable SSL/TLS to your broker, mount certs to /certs and use the provided celery-ssl.conf.
# - Reference the environment variables in your docker-compose or .env as needed.
# - Uncomment the COPY line and set SSL env vars for your broker (RabbitMQ/Redis).
# - See Celery and broker docs for advanced SSL usage and tuning.

# Healthcheck
HEALTHCHECK --interval=1m --timeout=20s --retries=3 --start-period=2m \
    CMD celery -A core inspect ping -t 10 || exit 1

# Run Celery beat
CMD ["celery", "-A", "core", "beat", "-l", "info"]