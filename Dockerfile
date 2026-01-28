FROM python:3.11-slim

WORKDIR /app

# Install kubectl
RUN apt-get update && apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && \
    apt-get clean

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY config/ ./config/

ENV PYTHONPATH=/app/src

# Create a simple health check script
RUN echo '#!/bin/bash\necho "AI Kustomize Agent is ready"\nwhile true; do sleep 3600; done' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Use bash entrypoint to keep container running
# For CLI usage, exec into the container: kubectl exec -it <pod> -- python src/main.py "your request"
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
