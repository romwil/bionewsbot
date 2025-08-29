# BioNewsBot Configuration Guide

## Overview

This guide covers all configuration options for BioNewsBot, including environment variables, service configurations, and advanced settings.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Application Configuration](#application-configuration)
- [Database Configuration](#database-configuration)
- [Redis Configuration](#redis-configuration)
- [API Keys & External Services](#api-keys--external-services)
- [Notification Settings](#notification-settings)
- [Security Configuration](#security-configuration)
- [Performance Tuning](#performance-tuning)
- [Logging Configuration](#logging-configuration)
- [Development vs Production](#development-vs-production)

## Environment Variables

### Core Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_ENV` | Application environment (development/staging/production) | `development` | Yes |
| `APP_NAME` | Application name | `BioNewsBot` | No |
| `APP_VERSION` | Application version | `1.0.0` | No |
| `SECRET_KEY` | Secret key for encryption/sessions | - | Yes |
| `API_KEY` | Main API authentication key | - | Yes |
| `DEBUG` | Enable debug mode | `false` | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` | No |

### Server Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Server host address | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `WORKERS` | Number of worker processes | `4` | No |
| `THREADS` | Threads per worker | `2` | No |
| `WORKER_CONNECTIONS` | Max simultaneous connections | `1000` | No |
| `TIMEOUT` | Request timeout in seconds | `300` | No |
| `KEEPALIVE` | Keep-alive timeout | `5` | No |

## Application Configuration

### Backend Configuration (FastAPI)

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "BioNewsBot"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API
    api_v1_prefix: str = "/api/v1"
    api_key_header: str = "X-API-Key"
    
    # CORS
    cors_origins: list = ["http://localhost:3000"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Frontend Configuration (Next.js)

```javascript
// next.config.js
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    NEXT_PUBLIC_APP_NAME: 'BioNewsBot',
    NEXT_PUBLIC_GA_ID: process.env.NEXT_PUBLIC_GA_ID,
  },
  
  // Performance optimizations
  images: {
    domains: ['bionewsbot.com', 'api.bionewsbot.com'],
    deviceSizes: [640, 750, 828, 1080, 1200],
    imageSizes: [16, 32, 48, 64, 96],
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ]
  },
}
```

## Database Configuration

### PostgreSQL Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection URL | - | Yes |
| `DB_HOST` | Database host | `postgres` | No |
| `DB_PORT` | Database port | `5432` | No |
| `DB_NAME` | Database name | `bionewsbot` | No |
| `DB_USER` | Database user | `postgres` | No |
| `DB_PASSWORD` | Database password | - | Yes |
| `DB_POOL_SIZE` | Connection pool size | `20` | No |
| `DB_MAX_OVERFLOW` | Max overflow connections | `40` | No |
| `DB_POOL_TIMEOUT` | Pool timeout in seconds | `30` | No |
| `DB_ECHO` | Echo SQL statements | `false` | No |

### Database Connection URL Format

```
postgresql://[user]:[password]@[host]:[port]/[database]?[options]

# Examples:
postgresql://postgres:password@localhost:5432/bionewsbot
postgresql://user:pass@db.example.com/bionewsbot?sslmode=require
```

### Advanced PostgreSQL Configuration

```sql
-- postgresql.conf
shared_buffers = 256MB              # 25% of RAM
effective_cache_size = 1GB          # 50-75% of RAM
work_mem = 4MB                      # RAM / (max_connections * 3)
maintenance_work_mem = 64MB         # RAM / 16
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1              # SSD = 1.1, HDD = 4
effective_io_concurrency = 200      # SSD = 200, HDD = 2
max_connections = 200

-- Performance tuning
logging_collector = on
log_statement = 'mod'
log_duration = on
log_min_duration_statement = 100    # Log queries slower than 100ms
```

## Redis Configuration

### Redis Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` | No |
| `REDIS_HOST` | Redis host | `redis` | No |
| `REDIS_PORT` | Redis port | `6379` | No |
| `REDIS_DB` | Redis database number | `0` | No |
| `REDIS_PASSWORD` | Redis password | - | No |
| `REDIS_MAX_CONNECTIONS` | Max connections | `50` | No |
| `REDIS_DECODE_RESPONSES` | Decode responses | `true` | No |

### Redis Configuration File

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

## API Keys & External Services

### Required API Keys

| Variable | Description | Required | Obtain From |
|----------|-------------|----------|-------------|
| `PUBMED_API_KEY` | PubMed E-utilities API key | Yes | [NCBI](https://www.ncbi.nlm.nih.gov/account/) |
| `NEWS_API_KEY` | News API key | Yes | [NewsAPI](https://newsapi.org/) |
| `CLINICALTRIALS_API_KEY` | ClinicalTrials.gov API | Optional | [CT.gov](https://clinicaltrials.gov/api/) |
| `OPENAI_API_KEY` | OpenAI API for NLP | Optional | [OpenAI](https://platform.openai.com/) |
| `GOOGLE_API_KEY` | Google Custom Search | Optional | [Google](https://developers.google.com/custom-search/) |

### API Configuration

```yaml
# api_config.yaml
apis:
  pubmed:
    base_url: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    rate_limit: 10  # requests per second
    timeout: 30
    retries: 3
    
  news_api:
    base_url: "https://newsapi.org/v2/"
    rate_limit: 500  # requests per day
    timeout: 20
    
  clinical_trials:
    base_url: "https://clinicaltrials.gov/api/query/"
    rate_limit: 5
    timeout: 60
```

## Notification Settings

### Slack Configuration

| Variable | Description | Required |
|----------|-------------|-----------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | No |
| `SLACK_BOT_TOKEN` | Slack bot user OAuth token | No |
| `SLACK_APP_TOKEN` | Slack app-level token | No |
| `SLACK_SIGNING_SECRET` | Slack signing secret | No |
| `SLACK_DEFAULT_CHANNEL` | Default notification channel | No |

### Email Configuration (SMTP)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SMTP_HOST` | SMTP server host | - | No |
| `SMTP_PORT` | SMTP server port | `587` | No |
| `SMTP_USER` | SMTP username | - | No |
| `SMTP_PASSWORD` | SMTP password | - | No |
| `SMTP_USE_TLS` | Use TLS | `true` | No |
| `SMTP_FROM_EMAIL` | From email address | - | No |
| `SMTP_FROM_NAME` | From name | `BioNewsBot` | No |

### Notification Templates

```python
# notification_config.py
NOTIFICATION_TEMPLATES = {
    "company_alert": {
        "slack": {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 {company_name} Alert"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "{alert_message}"
                    }
                }
            ]
        },
        "email": {
            "subject": "BioNewsBot Alert: {company_name}",
            "template": "company_alert.html"
        }
    }
}
```

## Security Configuration

### Authentication & Authorization

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JWT_SECRET_KEY` | JWT signing key | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `JWT_EXPIRATION_HOURS` | Token expiration | `24` | No |
| `PASSWORD_MIN_LENGTH` | Min password length | `8` | No |
| `PASSWORD_REQUIRE_SPECIAL` | Require special chars | `true` | No |
| `MAX_LOGIN_ATTEMPTS` | Max login attempts | `5` | No |
| `LOCKOUT_DURATION_MINUTES` | Account lockout time | `30` | No |

### CORS & Security Headers

```python
# security_config.py
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

CORS_CONFIG = {
    "allow_origins": ["https://bionewsbot.com"],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["*"],
    "max_age": 3600
}
```

## Performance Tuning

### Caching Configuration

```python
# cache_config.py
CACHE_CONFIG = {
    "default_ttl": 3600,  # 1 hour
    "company_data_ttl": 7200,  # 2 hours
    "news_feed_ttl": 300,  # 5 minutes
    "api_response_ttl": 600,  # 10 minutes
    "static_asset_ttl": 86400,  # 24 hours
}

# Cache key patterns
CACHE_KEYS = {
    "company": "company:{company_id}",
    "news": "news:{category}:{page}",
    "intelligence": "intel:{company_id}:{period}",
    "user_session": "session:{session_id}"
}
_routes": {
        "news_scraper": {
            "task": "tasks.scrape_news",
            "schedule": {"minute": "*/15"},
        },
        "pubmed_sync": {
            "task": "tasks.sync_pubmed",
            "schedule": {"hour": "*/6"},
        },
        "sentiment_analysis": {
            "task": "tasks.analyze_sentiment",
            "schedule": {"hour": "*/2"},
        },
        "report_generation": {
            "task": "tasks.generate_reports",
            "schedule": {"day_of_week": 1, "hour": 9},
        }
    },
    "task_time_limit": 3600,
    "task_soft_time_limit": 3000,
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 1000,
}
```

## Logging Configuration

### Log Levels and Formats

```python
# logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "bionewsbot": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file", "error_file"],
    },
}
```

### Structured Logging

```python
# structured_logging.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## Development vs Production

### Development Configuration (.env.development)

```bash
# Development Environment
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Local services
DATABASE_URL=postgresql://postgres:password@localhost:5432/bionewsbot_dev
REDIS_URL=redis://localhost:6379/0

# Development API keys (limited rate)
PUBMED_API_KEY=dev_key_here
NEWS_API_KEY=dev_key_here

# Disable rate limiting in dev
RATE_LIMIT_ENABLED=false

# Enable hot reload
RELOAD=true
WORKERS=1
```

### Production Configuration (.env.production)

```bash
# Production Environment
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Production database with SSL
DATABASE_URL=postgresql://user:pass@db.bionewsbot.com:5432/bionewsbot?sslmode=require

# Redis cluster
REDIS_URL=redis://redis-cluster.bionewsbot.com:6379/0

# Production API keys
PUBMED_API_KEY=prod_key_here
NEWS_API_KEY=prod_key_here

# Security
SECRET_KEY=generate-strong-secret-key
ALLOWED_HOSTS=bionewsbot.com,www.bionewsbot.com

# Performance
WORKERS=8
THREADS=4
WORKER_CONNECTIONS=2000
```

### Environment-Specific Features

```python
# config/environments.py
from functools import lru_cache
from typing import Dict, Any

@lru_cache()
def get_environment_config() -> Dict[str, Any]:
    env = os.getenv("APP_ENV", "development")
    
    configs = {
        "development": {
            "debug": True,
            "testing": True,
            "database_echo": True,
            "cache_enabled": False,
            "rate_limit_enabled": False,
            "email_backend": "console",
            "frontend_url": "http://localhost:3000",
        },
        "staging": {
            "debug": False,
            "testing": True,
            "database_echo": False,
            "cache_enabled": True,
            "rate_limit_enabled": True,
            "email_backend": "smtp",
            "frontend_url": "https://staging.bionewsbot.com",
        },
        "production": {
            "debug": False,
            "testing": False,
            "database_echo": False,
            "cache_enabled": True,
            "rate_limit_enabled": True,
            "email_backend": "smtp",
            "frontend_url": "https://bionewsbot.com",
        },
    }
    
    return configs.get(env, configs["development"])
```

## Configuration Validation

### Startup Validation

```python
# config/validator.py
from typing import List, Tuple
import os
import sys

def validate_configuration() -> Tuple[bool, List[str]]:
    """Validate required configuration on startup."""
    errors = []
    
    # Required environment variables
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "API_KEY",
        "PUBMED_API_KEY",
        "NEWS_API_KEY",
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate database connection
    try:
        from sqlalchemy import create_engine
        engine = create_engine(os.getenv("DATABASE_URL"))
        engine.connect()
    except Exception as e:
        errors.append(f"Database connection failed: {str(e)}")
    
    # Validate Redis connection
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
    except Exception as e:
        errors.append(f"Redis connection failed: {str(e)}")
    
    return len(errors) == 0, errors

# Run validation on startup
if __name__ == "__main__":
    valid, errors = validate_configuration()
    if not valid:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
```

## Configuration Best Practices

1. **Never commit secrets**: Use `.env` files and add them to `.gitignore`
2. **Use environment-specific files**: `.env.development`, `.env.production`
3. **Validate on startup**: Check all required configuration before starting
4. **Use defaults wisely**: Provide sensible defaults for optional settings
5. **Document everything**: Keep this guide updated with new settings
6. **Rotate secrets regularly**: Especially API keys and passwords
7. **Monitor configuration**: Log configuration changes and access
8. **Use secrets management**: Consider HashiCorp Vault or AWS Secrets Manager for production

## Configuration Management Tools

### Using Docker Secrets

```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - db_password
      - api_key
    environment:
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
      API_KEY_FILE: /run/secrets/api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt
```

### Using Kubernetes ConfigMaps and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bionewsbot-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  WORKERS: "4"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: bionewsbot-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@db:5432/bionewsbot"
  SECRET_KEY: "your-secret-key"
  API_KEY: "your-api-key"
```

## Support

For configuration assistance:
- Documentation: https://docs.bionewsbot.com/configuration
- Config Examples: https://github.com/romwil/bionewsbot/tree/main/config
- Support Email: config@bionewsbot.com

