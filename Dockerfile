FROM python:3.11-slim

WORKDIR /app

# Install kubectl with explicit version (more reliable)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LO "https://dl.k8s.io/release/v1.29.0/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY config/ ./config/
COPY examples/ ./examples/

ENV PYTHONPATH=/app/src

# Create a simple health check script that also starts the API server
RUN printf '#!/bin/bash\necho "🚀 Starting AI Kustomize Agent..."\ncd /app && python -m api.server\n' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

EXPOSE 8000

# Start the FastAPI server
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
