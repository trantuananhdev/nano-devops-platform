# health-api Service
# Lightweight, resource-efficient service (<100MB RAM)

# --- Stage 1: Builder ---
FROM python:3.11-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev

# Install Python dependencies into a temporary directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final ---
FROM python:3.11-alpine

WORKDIR /app

# Copy only the installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ /app/

# Install runtime dependencies (wget for healthcheck)
RUN apk add --no-cache wget

# Run as non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8080

# Environment variables for Gunicorn
ENV GUNICORN_WORKERS=2
ENV GUNICORN_THREADS=4
ENV GUNICORN_BIND=0.0.0.0:8080

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

# Run application using Gunicorn (Production-ready WSGI server)
CMD ["sh", "-c", "gunicorn --workers $GUNICORN_WORKERS --threads $GUNICORN_THREADS --bind $GUNICORN_BIND app:app"]
