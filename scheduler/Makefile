# BioNewsBot Scheduler Service Makefile

.PHONY: help setup install dev test lint format clean docker-build docker-up docker-down docker-logs

# Default target
help:
@echo "BioNewsBot Scheduler Service Commands:"
@echo "  make setup        - Set up development environment"
@echo "  make install      - Install dependencies"
@echo "  make dev          - Run development servers"
@echo "  make test         - Run tests"
@echo "  make lint         - Run linting"
@echo "  make format       - Format code"
@echo "  make clean        - Clean temporary files"
@echo "  make docker-build - Build Docker images"
@echo "  make docker-up    - Start Docker services"
@echo "  make docker-down  - Stop Docker services"
@echo "  make docker-logs  - View Docker logs"

# Setup development environment
setup:
python -m venv venv
. venv/bin/activate && pip install --upgrade pip
. venv/bin/activate && pip install -r requirements.txt
cp .env.example .env
@echo "Setup complete! Edit .env file with your configuration."

# Install dependencies
install:
pip install -r requirements.txt

# Run development servers
dev:
@echo "Starting Redis..."
docker run -d --name bionewsbot-redis -p 6379:6379 redis:7-alpine || true
@echo "Starting scheduler service..."
python scheduler_service.py &
@echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info &
@echo "Starting Flower monitoring..."
celery -A celery_app flower &
@echo "All services started! Check logs for details."

# Run scheduler only
scheduler:
python scheduler_service.py

# Run worker only
worker:
python celery_worker.py

# Run multiple workers
workers:
celery -A celery_app worker --loglevel=info --concurrency=2 -n worker1@%h &
celery -A celery_app worker --loglevel=info --concurrency=2 -n worker2@%h &
celery -A celery_app worker --loglevel=info --concurrency=2 -n worker3@%h &

# Run tests
test:
pytest -v

# Run tests with coverage
test-cov:
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
test-file:
pytest -v $(FILE)

# Lint code
lint:
flake8 . --exclude=venv,__pycache__
mypy . --exclude venv

# Format code
format:
black .
isort .

# Clean temporary files
clean:
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete
find . -type d -name "*.egg-info" -delete
rm -rf .pytest_cache
rm -rf .coverage
rm -rf htmlcov
rm -rf .mypy_cache

# Docker commands
docker-build:
docker-compose build

# Start all services
docker-up:
docker-compose up -d
@echo "Services started! Check status with 'make docker-ps'"

# Start with specific scale
docker-scale:
docker-compose up -d --scale worker=$(WORKERS)

# Stop all services
docker-down:
docker-compose down

# View logs
docker-logs:
docker-compose logs -f

# View specific service logs
docker-logs-service:
docker-compose logs -f $(SERVICE)

# Show running containers
docker-ps:
docker-compose ps

# Execute command in container
docker-exec:
docker-compose exec $(SERVICE) $(CMD)

# Restart services
docker-restart:
docker-compose restart

# Remove volumes (careful!)
docker-clean:
docker-compose down -v

# Production deployment
deploy:
@echo "Deploying to production..."
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
@echo "Deployment complete!"

# Database migrations (if needed)
migrate:
python -m alembic upgrade head

# Create new migration
migration:
python -m alembic revision --autogenerate -m "$(MSG)"

# Monitor services
monitor:
@echo "Opening monitoring dashboards..."
@echo "Flower (Celery): http://localhost:5555"
@echo "Prometheus: http://localhost:9091"
@echo "Grafana: http://localhost:3001"
@echo "Health Check: http://localhost:8001/health"

# Show scheduled jobs
jobs:
curl -s http://localhost:8001/stats | jq '.scheduled_jobs'

# Trigger manual analysis
analyze:
curl -X POST http://localhost:8001/trigger/analysis/$(COMPANY)

# Generate report
report:
curl -X POST http://localhost:8001/trigger/report

# Check health
health:
curl -s http://localhost:8001/health | jq .

# View metrics
metrics:
curl -s http://localhost:9090/metrics | grep bionewsbot
