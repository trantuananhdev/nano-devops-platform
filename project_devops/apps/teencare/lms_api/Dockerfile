FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:/app/lms_api

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY lms_api/requirements.txt /app/lms_api-requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/lms_api-requirements.txt

COPY src /app/src
COPY lms_api /app/lms_api
COPY samples /app/samples

EXPOSE 8000

WORKDIR /app/lms_api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

