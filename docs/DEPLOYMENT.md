# BioNewsBot Deployment Guide

## Overview

This guide covers deploying BioNewsBot to production environments, including cloud platforms, on-premises servers, and Kubernetes clusters.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platform Deployment](#cloud-platform-deployment)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Database Setup](#database-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling Considerations](#scaling-considerations)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: Minimum 4 cores, recommended 8+ cores
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: 50GB+ SSD storage
- **OS**: Ubuntu 20.04+ or RHEL 8+
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### Required Services

- PostgreSQL 15+
- Redis 7+
- SMTP server for email notifications
- Slack webhook URL (optional)

## Deployment Options

### 1. Single Server Deployment

Best for: Small to medium deployments, proof of concept

```bash
# Clone repository
git clone https://github.com/romwil/bionewsbot.git
cd bionewsbot

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Deploy with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Multi-Server Deployment

Best for: High availability, large scale deployments

- **Load Balancer**: HAProxy or Nginx
- **App Servers**: Multiple Docker hosts
- **Database**: PostgreSQL cluster
- **Cache**: Redis Sentinel

### 3. Kubernetes Deployment

Best for: Cloud-native, auto-scaling environments

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress.yaml
```

## Environment Configuration

### Essential Environment Variables

```bash
# Application Settings
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/bionewsbot
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50

# External APIs
PUBMED_API_KEY=your-pubmed-key
NEWS_API_KEY=your-news-api-key
CLINICALTRIALS_API_KEY=your-ct-key

# Notification Settings
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@bionewsbot.com
SMTP_PASSWORD=your-smtp-password

# Security
ALLOWED_HOSTS=bionewsbot.com,www.bionewsbot.com
CORS_ORIGINS=https://bionewsbot.com
CSRF_TRUSTED_ORIGINS=https://bionewsbot.com

# Performance
WORKERS=4
THREADS=2
WORKER_CONNECTIONS=1000
```

### Production Configuration File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - APP_ENV=production
      - WORKERS=4
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    restart: always

  frontend:
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 2G
    restart: always

  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups/postgres:/backups
    environment:
      - POSTGRES_REPLICATION_MODE=master
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=repl_password
    restart: always

  redis:
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: always

  nginx:
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/usr/share/nginx/html/static:ro
    ports:
      - "80:80"
      - "443:443"
    restart: always

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

## Docker Deployment

### 1. Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | bash

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Deploy Application

```bash
# Clone and configure
git clone https://github.com/romwil/bionewsbot.git
cd bionewsbot
cp .env.example .env
# Edit .env with production values

# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py
```

### 3. Health Checks

```bash
# Check all services are running
docker-compose ps

# Run health check script
python health-check.py

# Check logs
docker-compose logs -f --tail=100
```

## Kubernetes Deployment

### 1. Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 2. Deploy with Helm

```bash
# Add Helm repository
helm repo add bionewsbot https://charts.bionewsbot.com
helm repo update

# Install BioNewsBot
helm install bionewsbot bionewsbot/bionewsbot \
  --namespace bionewsbot \
  --create-namespace \
  --values values.prod.yaml
```

### 3. Kubernetes Manifests

Example deployment manifest (`k8s/deployments/backend.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: bionewsbot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: bionewsbot/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bionewsbot-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Cloud Platform Deployment

### AWS Deployment

```bash
# Using AWS ECS
aws ecs create-cluster --cluster-name bionewsbot-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster bionewsbot-cluster \
  --service-name bionewsbot-service \
  --task-definition bionewsbot:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### Google Cloud Platform

```bash
# Deploy to Cloud Run
gcloud run deploy bionewsbot \
  --image gcr.io/project-id/bionewsbot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Deployment

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group bionewsbot-rg \
  --name bionewsbot \
  --image bionewsbot/app:latest \
  --dns-name-label bionewsbot \
  --ports 80 443
```

## SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d bionewsbot.com -d www.bionewsbot.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name bionewsbot.com;

    ssl_certificate /etc/letsencrypt/live/bionewsbot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bionewsbot.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
K Stack

```bash
# Deploy ELK stack
docker-compose -f docker-compose.monitoring.yml up -d

# Configure Filebeat
docker-compose exec filebeat filebeat setup
```

### Application Logs

```python
# Configure structured logging
import structlog

logger = structlog.get_logger()

logger.info(
    "api_request",
    method="GET",
    path="/api/v1/companies",
    user_id=user_id,
    duration_ms=duration
)
```

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

# Database backup
docker-compose exec -T postgres pg_dump -U postgres bionewsbot | gzip > backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Redis backup
docker-compose exec -T redis redis-cli BGSAVE
docker cp bionewsbot_redis_1:/data/dump.rdb backups/redis_$(date +%Y%m%d_%H%M%S).rdb

# Upload to S3
aws s3 sync backups/ s3://bionewsbot-backups/

# Cleanup old backups (keep 30 days)
find backups/ -type f -mtime +30 -delete
```

### Restore Procedure

```bash
# Restore database
gunzip -c backups/db_20240115_120000.sql.gz | docker-compose exec -T postgres psql -U postgres bionewsbot

# Restore Redis
docker cp backups/redis_20240115_120000.rdb bionewsbot_redis_1:/data/dump.rdb
docker-compose restart redis
```

## Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 4
      update_config:
        parallelism: 2
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  celery_worker:
    deploy:
      replicas: 6
    command: celery -A app.celery worker --loglevel=info --concurrency=4
```

### Load Balancing

```nginx
# nginx/upstream.conf
upstream backend_servers {
    least_conn;
    server backend_1:8000 weight=3;
    server backend_2:8000 weight=3;
    server backend_3:8000 weight=2;
    server backend_4:8000 weight=2;
    
    keepalive 32;
}
```

### Database Scaling

```bash
# PostgreSQL read replicas
docker run -d \
  --name postgres-replica \
  -e POSTGRES_REPLICATION_MODE=slave \
  -e POSTGRES_MASTER_HOST=postgres-master \
  -e POSTGRES_REPLICATION_USER=replicator \
  -e POSTGRES_REPLICATION_PASSWORD=repl_password \
  postgres:15
```

## Security Best Practices

### 1. Environment Security

```bash
# Use secrets management
docker secret create db_password ./secrets/db_password.txt
docker secret create api_key ./secrets/api_key.txt

# Reference in docker-compose
services:
  backend:
    secrets:
      - db_password
      - api_key
    environment:
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
      API_KEY_FILE: /run/secrets/api_key
```

### 2. Network Security

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
  database:
    driver: bridge
    internal: true

services:
  nginx:
    networks:
      - frontend
  backend:
    networks:
      - frontend
      - backend
      - database
  postgres:
    networks:
      - database
```

### 3. Container Security

```dockerfile
# Run as non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

USER appuser

# Security scanning
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

### 4. API Security

```python
# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/companies")
@limiter.limit("100/hour")
async def get_companies(request: Request):
    pass
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check container status
docker ps -a

# Inspect container
docker inspect bionewsbot_backend_1
```

#### 2. Database Connection Issues

```bash
# Test database connection
docker-compose exec backend python -c "from app.database import engine; engine.connect()"

# Check PostgreSQL logs
docker-compose logs postgres

# Verify network connectivity
docker-compose exec backend ping postgres
```

#### 3. Memory Issues

```bash
# Check memory usage
docker stats

# Increase memory limits
docker update --memory="4g" --memory-swap="4g" container_name
```

#### 4. Performance Issues

```bash
# Profile application
docker-compose exec backend python -m cProfile -o profile.stats app.main

# Analyze slow queries
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Debug Mode

```yaml
# docker-compose.debug.yml
services:
  backend:
    command: python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload
    ports:
      - "5678:5678"  # Debug port
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

### Health Check Scripts

```python
#!/usr/bin/env python3
# health_check.py

import requests
import sys

checks = [
    ("Backend API", "http://localhost:8000/health"),
    ("Frontend", "http://localhost:3000/api/health"),
    ("PostgreSQL", "http://localhost:8000/api/v1/health/db"),
    ("Redis", "http://localhost:8000/api/v1/health/cache"),
]

failed = False
for name, url in checks:
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ {name}: OK")
        else:
            print(f"✗ {name}: Failed (Status: {response.status_code})")
            failed = True
    except Exception as e:
        print(f"✗ {name}: Failed ({str(e)})")
        failed = True

sys.exit(1 if failed else 0)
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Weekly maintenance script
#!/bin/bash

# 1. Update containers
docker-compose pull
docker-compose up -d

# 2. Clean up old images
docker image prune -a -f --filter "until=168h"

# 3. Vacuum database
docker-compose exec postgres vacuumdb -U postgres -d bionewsbot -z

# 4. Rotate logs
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
find logs/ -name "*.gz" -mtime +30 -delete

# 5. Check disk space
df -h | grep -E "(Filesystem|docker)"
```

### Update Procedure

```bash
# 1. Backup current state
./scripts/backup.sh

# 2. Pull latest changes
git pull origin main

# 3. Build new images
docker-compose build

# 4. Run database migrations
docker-compose run --rm backend alembic upgrade head

# 5. Deploy with zero downtime
docker-compose up -d --no-deps --scale backend=2 backend

# 6. Health check
python health_check.py

# 7. Remove old containers
docker-compose up -d --no-deps --remove-orphans
```

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups scheduled
- [ ] Monitoring configured
- [ ] Log aggregation setup
- [ ] Security scanning enabled
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Health checks implemented
- [ ] Error tracking setup (Sentry)
- [ ] Performance monitoring (APM)
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security audit performed
- [ ] Documentation updated

## Support

For deployment support:
- Email: devops@bionewsbot.com
- Slack: #deployment-help
- Documentation: https://docs.bionewsbot.com/deployment

