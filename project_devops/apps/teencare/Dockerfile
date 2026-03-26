FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create volume for samples and outputs
VOLUME ["/app/samples", "/app/outputs"]

# Expose port for Streamlit
EXPOSE 8501

# Default entrypoint (keep as python -m for CLI use, but we can override in compose)
ENTRYPOINT ["python", "-m"]

# Default command: run the pipeline help
CMD ["teencare_ai", "--help"]
