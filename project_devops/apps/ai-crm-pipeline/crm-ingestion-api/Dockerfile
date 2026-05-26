# crm-ingestion-api — FastAPI async ingestion (<120MB RAM)
FROM python:3.11-alpine AS builder

WORKDIR /app
RUN apk add --no-cache gcc musl-dev

COPY crm-ingestion-api/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app
COPY --from=builder /install /usr/local
COPY crm-ingestion-api/src/ /app/
COPY crm-demo-simulator/templates.json /app/templates.json
COPY crm-demo-simulator/scenarios.json /app/scenarios.json

RUN apk add --no-cache wget \
    && addgroup -g 1000 appuser \
    && adduser -D -u 1000 -G appuser appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

ENV PORT=8080
ENV REDIS_URL=redis://platform-redis:6379/0

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=15s \
  CMD wget -qO /dev/null http://localhost:8080/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
