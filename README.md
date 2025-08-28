# BioNewsBot - Life Sciences Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-green.svg)](https://www.python.org/)

BioNewsBot is an AI-powered platform that monitors, analyzes, and delivers insights about biotechnology companies by aggregating data from scientific publications, news sources, and market intelligence.

## 🏗️ Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Next.js        │────▶│  FastAPI        │────▶│  PostgreSQL     │
│  Frontend       │     │  Backend API    │     │  Database       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        ▲
         │                       │                        │
         │              ┌─────────────────┐               │
         │              │                 │               │
         └─────────────▶│  Redis Cache    │◀──────────────┘
                        │                 │
                        └─────────────────┘
                                 ▲
                                 │
                    ┌────────────┴────────────┐
                    │                         │
           ┌─────────────────┐      ┌─────────────────┐
           │                 │      │                 │
           │  Scheduler      │      │  Notifications  │
           │  (Celery)       │      │  (Slack)        │
           │                 │      │                 │
           └─────────────────┘      └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB free disk space

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/bionewsbot.git
cd bionewsbot
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, update:
# - API keys (OpenAI, PubMed, News API)
# - Slack tokens
# - Database passwords
nano .env
```

### 3. Run Setup

```bash
# Run the automated setup script
./setup.sh

# This will:
# - Check system requirements
# - Build all Docker images
# - Start infrastructure services
# - Run database migrations
# - Seed initial data
# - Start all services
# - Verify health status
```

### 4. Access the Platform

- **Frontend Dashboard**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Notification Service**: http://localhost:8001/docs

## 📦 Services

### Core Services

| Service | Description | Port | Technology |
|---------|-------------|------|------------|
| Frontend | Web dashboard for monitoring and insights | 3000 | Next.js 14, TypeScript |
| Backend | REST API for data management and analysis | 8000 | FastAPI, Python 3.11 |
| Database | Primary data storage | 5432 | PostgreSQL 16 |
| Cache | Session and data caching | 6379 | Redis 7 |

### Processing Services

| Service | Description | Technology |
|---------|-------------|------------|
| Scheduler | Automated analysis and data collection | Celery, APScheduler |
| Notifications | Slack integration for alerts | FastAPI, Slack SDK |

### Optional Services (Production)

| Service | Description | Port |
|---------|-------------|------|
| Nginx | Reverse proxy and load balancer | 80/443 |
| Prometheus | Metrics collection | 9090 |
| Grafana | Metrics visualization | 3001 |

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Core Settings
ENVIRONMENT=production
DEBUG=false

# Database
POSTGRES_DB=bionewsbot
POSTGRES_USER=bionewsbot
POSTGRES_PASSWORD=secure-password

# API Keys
OPENAI_API_KEY=sk-...
PUBMED_API_KEY=...
NEWS_API_KEY=...

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

### Service Configuration

Each service can be configured through:
- Environment variables
- Configuration files in service directories
- Docker Compose overrides

## 🧪 Testing

### Run Integration Tests

```bash
# Run the complete integration test suite
python tests/integration/test_integration.py

# Run with custom API URL
API_URL=http://localhost:8000 python tests/integration/test_integration.py
```

### Run Unit Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test
```

## 📊 Monitoring

### Enable Monitoring Stack

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Access monitoring tools
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### Health Checks

All services include health check endpoints:

```bash
# Check all services
curl http://localhost:8000/health  # Backend
curl http://localhost:3000/api/health  # Frontend
curl http://localhost:8001/webhooks/health  # Notifications
```

## 🚢 Production Deployment

### 1. Server Requirements

- Ubuntu 20.04+ or similar Linux distribution
- 16GB RAM minimum
- 100GB SSD storage
- Docker and Docker Compose installed

### 2. Security Setup

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash bionewsbot
sudo usermod -aG docker bionewsbot

# Set up firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 3. SSL/TLS Configuration

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx configuration with SSL
```

### 4. Production Environment

```bash
# Copy production environment template
cp .env.production.example .env

# Update with production values
# - Strong passwords
# - Production API keys
# - Domain configuration
```

### 5. Deploy

```bash
# Run setup in production mode
ENVIRONMENT=production ./setup.sh

# Enable auto-restart
sudo systemctl enable docker
```

### 6. Backup Strategy

```bash
# Database backups
./scripts/backup-database.sh

# Schedule daily backups
crontab -e
0 2 * * * /path/to/bionewsbot/scripts/backup-database.sh
```

## 🛠️ Maintenance

### Common Commands

```bash
# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Update service
docker-compose build [service]
docker-compose up -d [service]

# Database operations
docker-compose exec postgres psql -U bionewsbot

# Clear cache
docker-compose exec redis redis-cli FLUSHALL
```

### Troubleshooting

#### Service won't start
```bash
# Check logs
docker-compose logs [service]

# Check health
docker-compose ps

# Rebuild service
docker-compose build --no-cache [service]
```

#### Database connection issues
```bash
# Test connection
docker-compose exec postgres pg_isready

# Check credentials
docker-compose exec backend python -c "from app.database import test_connection; test_connection()"
```

## 📚 API Documentation

### Main Endpoints

- `GET /api/v1/companies` - List companies
- `POST /api/v1/companies` - Create company
- `POST /api/v1/analyses` - Trigger analysis
- `GET /api/v1/insights` - Get insights
- `POST /api/v1/notifications` - Send notification

Full API documentation available at http://localhost:8000/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT API
- PubMed for scientific literature access
- Slack for notification platform
- All open-source contributors

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/bionewsbot/issues)
- Email: support@bionewsbot.com
