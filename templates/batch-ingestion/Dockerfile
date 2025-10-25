# Use a lightweight Python base
FROM python:3.10-slim

# Metadata
LABEL maintainer="data-mcp-server team"
WORKDIR /app

# Install system deps required for common python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install runtime Python deps needed by the runner.
# Keep list minimal; add extras as needed for production (e.g. fastparquet).
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir boto3 pandas pyarrow python-dotenv pyyaml

# Copy template runner and example config into the image
COPY templates/batch-ingestion/runner.py /app/runner.py
COPY templates/batch-ingestion/pipeline.yaml /app/pipeline.yaml

# Create a place for data if running locally-mounted volumes
RUN mkdir -p /app/data /app/out

# Entrypoint runs a single pipeline invocation using supplied config
# Usage:
#  docker build -t batch-ingest:latest .
#  docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/out:/app/out batch-ingest:latest --config /app/pipeline.yaml
ENTRYPOINT ["python", "/app/runner.py"]
CMD ["--config", "/app/pipeline.yaml"]
