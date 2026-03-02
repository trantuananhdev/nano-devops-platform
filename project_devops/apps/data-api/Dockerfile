# Data API Service - HTTP API with PostgreSQL integration
# Lightweight, resource-efficient service (<100MB RAM)

FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apk add --no-cache postgresql-dev gcc musl-dev

# Install Python dependencies
RUN pip install --no-cache-dir flask prometheus-client psycopg2-binary

# Copy application code
COPY src/ /app/

# Run as non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

# Run application
CMD ["python", "app.py"]
