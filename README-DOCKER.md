# BioNewsBot Docker Infrastructure

Complete Docker setup for the BioNewsBot microservices architecture.

## Architecture Overview

- **Frontend**: Next.js application (Port 3000)
- **Backend API**: FastAPI Python application (Port 8000)
- **Scheduler**: Python-based worker service for scheduled tasks
- **PostgreSQL**: Database with persistent storage (Port 5432)
- **Redis**: Cache and message broker (Port 6379)
- **Nginx**: Reverse proxy (Ports 80/443)

## Quick Start

1. Clone the repository and navigate to the project directory:
```bash
cd /root/bionewsbot
```

2. Copy the environment template and configure:
```bash
cp .env.example .env
# Edit .env with your actual values
```

3. Build and start all services:
```bash
docker-compose up -d --build
```

4. Check service health:
```bash
docker-compose ps
docker-compose logs -f
```

## Service URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Common Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Rebuild specific service
```bash
docker-compose up -d --build backend
```

### Execute commands in containers
```bash
# Backend shell
docker-compose exec backend bash

# Database shell
docker-compose exec postgres psql -U bionewsbot

# Redis CLI
docker-compose exec redis redis-cli
```

### Database migrations
```bash
docker-compose exec backend alembic upgrade head
```

## Data Persistence

Data is persisted using Docker volumes:
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files
- `backend_logs`: Backend application logs
- `scheduler_logs`: Scheduler service logs
- `frontend_cache`: Next.js build cache
- `nginx_logs`: Nginx access and error logs

## Environment Variables

Key environment variables (see .env.example for full list):

- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `SECRET_KEY`: Application secret key
- `API_KEY`: API authentication key
- `CORS_ORIGINS`: Allowed CORS origins

## Health Checks

All services include health checks:
- Frontend: `http://localhost:3000/api/health`
- Backend: `http://localhost:8000/health`
- Nginx: `http://localhost/health`

## Production Deployment

1. Update `.env` with production values
2. Configure SSL certificates in Nginx
3. Set proper domain names
4. Enable firewall rules
5. Set up monitoring (Prometheus/Grafana)
6. Configure backup strategies

## Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs [service_name]

# Verify environment variables
docker-compose config
```

### Database connection issues
```bash
# Check if database is ready
docker-compose exec postgres pg_isready

# Verify credentials
docker-compose exec postgres psql -U bionewsbot -c "\l"
```

### Port conflicts
```bash
# Check port usage
sudo lsof -i :3000
sudo lsof -i :8000
```

## Security Notes

1. Change all default passwords in production
2. Use SSL/TLS certificates for HTTPS
3. Configure firewall rules
4. Regularly update base images
5. Implement rate limiting
6. Use secrets management for sensitive data

## Backup and Restore

### Backup database
```bash
docker-compose exec postgres pg_dump -U bionewsbot bionewsbot > backup.sql
```

### Restore database
```bash
docker-compose exec -T postgres psql -U bionewsbot bionewsbot < backup.sql
```

## Development Tips

1. Use `docker-compose.override.yml` for local overrides
2. Mount source code as volumes for hot reloading
3. Use Docker BuildKit for faster builds: `DOCKER_BUILDKIT=1`
4. Prune unused resources: `docker system prune -a`

## Support

For issues or questions:
1. Check service logs
2. Verify environment configuration
3. Ensure all dependencies are installed
4. Check Docker and Docker Compose versions
