# =====================================
# Multi-stage build for AI Kustomize Agent
# Includes: Python API + React Frontend
# =====================================

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python API Server
FROM python:3.11-slim

WORKDIR /app

# Install kubectl and nginx
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates nginx && \
    curl -LO "https://dl.k8s.io/release/v1.29.0/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY config/ ./config/
COPY examples/ ./examples/

# Copy built frontend
COPY --from=frontend-builder /web/dist /app/static

ENV PYTHONPATH=/app/src

# Nginx config to serve frontend and proxy API
RUN echo 'server { \
    listen 80; \
    root /app/static; \
    index index.html; \
    location / { \
    try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
    proxy_pass http://127.0.0.1:8000/; \
    proxy_http_version 1.1; \
    proxy_set_header Host $host; \
    proxy_set_header X-Real-IP $remote_addr; \
    } \
    location /health { \
    proxy_pass http://127.0.0.1:8000/health; \
    } \
    }' > /etc/nginx/sites-available/default

# Startup script: Run both API and Nginx
RUN printf '#!/bin/bash\n\
    echo "🚀 Starting AI Kustomize Agent..."\n\
    cd /app && python -m api.server &\n\
    sleep 2\n\
    nginx -g "daemon off;"\n' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

EXPOSE 80 8000

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
