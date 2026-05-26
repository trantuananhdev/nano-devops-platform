FROM python:3.11-alpine AS builder

WORKDIR /app
RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app
RUN apk add --no-cache libpq
COPY --from=builder /install /usr/local
COPY src/ /app/

RUN addgroup -g 1000 appuser \
    && adduser -D -u 1000 -G appuser appuser \
    && chown -R appuser:appuser /app

USER appuser

ENV METRICS_PORT=9100
EXPOSE 9100

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=20s \
  CMD wget -qO /dev/null http://localhost:9100/metrics || exit 1

CMD ["python", "worker.py"]
