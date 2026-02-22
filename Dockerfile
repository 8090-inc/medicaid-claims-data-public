FROM python:3.11-slim

LABEL maintainer="Rohit Kelapure"
LABEL description="Medicaid FWA Analytics Pipeline"

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY config/ config/
COPY utils/ utils/
COPY scripts/ scripts/
COPY config.yml .
COPY setup_project_foundation.py .

# Create output directories
RUN python3 setup_project_foundation.py

# Data volume mount points
VOLUME ["/app/data", "/app/output", "/app/reference_data", "/app/logs"]

# Default: run the full pipeline
ENTRYPOINT ["python3", "scripts/run_all.py"]
CMD []
